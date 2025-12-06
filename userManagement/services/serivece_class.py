from userManagement.models import *
from userManagement.serializer import * 
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
from itemmaster.Utils.CommanUtils import *
from itemmaster.serializer import *

class PaymentVoucherService:
    def __init__(self, kwargs, status, info):
        self.kwargs = kwargs
        self.status_text = status
        self.status = status
        self.info = info
        
        self.payment_voucher = None
        self.against_invoice_details_serializer = {}
        self.advance_details_serializer = {}
        self.payment_voucher_line_serializer = []
        

        self.against_invoice_details_instance = {}
        self.advance_details_instance = {}
        self.payment_voucher_line_instance = []
        self.old_against_invoice_details_instance = []
        self.old_advance_details_instance = []
        self.purchase_invoice = []

        self.success = False
        self.errors = []
    
    """MAIN CONTROLLER"""
    def process(self) -> dict:
        with transaction.atomic():
            try:
                if self.status_text in ["Draft", "Submit"]:
                    if not self.get_payment_voucher(): return self.response()
                    print("----1")
                    if not self.validate_required_fields(): return self.response()
                    print("----2")
                    if not self.validate_numbering(): return self.response()
                    if not self.update_status_instance(): return self.response()

                    # Child validations
                    if not self.validate_pv_line(): return self.response()
                    print("----5")

                    if not self.save_pv_line(): return self.response()
                    
                    # Save main voucher
                    if not self.save_payment_voucher(): return self.response()

                    if self.status_text == 'Submit':
                        if not self.save_purchase_paid_detail(): return self.response()
                    self.success = True
                    return self.response()
                else:
                    self.errors.append(f"{self.status_text} Unexpeted status.")
                return self.response()
            
            except Exception as e:
                self.errors.append(f"Unexpected server error: {str(e)}")
                return self.response()

    """FETCH MAIN DOCUMENT"""
    def get_payment_voucher(self) ->bool:
        try:
            if "id" in self.kwargs and self.kwargs.get("id"):
                pv = PaymentVoucher.objects.filter(id=self.kwargs.get("id")).first()

                if not pv:
                    self.errors.append("Payment Voucher not found.")
                    return False
                
                # State protection rules
                current = pv.status.name

                if self.status_text == "Draft" and current in ["Submit", "Canceled"]:
                    self.errors.append(
                        f"Already {current}. Cannot move back to Draft."
                    )

                if self.status_text == "Submit" and current == "Canceled":
                    self.errors.append(
                        f"Already Canceled. Cannot Submit again."
                    )

                if self.errors:
                    return False

                self.payment_voucher = pv
                # self.old_advance_details_instance = pv.paymentvoucheradvancedetails_set.all()
                # self.old_against_invoice_details_instance = pv.paymentvoucheragainstinvoice_set.all()
                return True

            # No ID = new record
            return True

        except Exception as e:
            self.errors.append(f"Error on fetch receipt voucher: {str(e)}")
            return False
    
    """UPDATE THE STATUS"""
    def update_status_instance(self) ->bool:
        try:
            status = CommanStatus.objects.filter(
            name=self.status_text, table="Payment Voucher"
            ).first()

            if not status:
                self.errors.append(f"Ask developer to add status '{self.status_text}' in CommanStatus.")
                return False
            
            self.kwargs["status"] = status.id
            self.status= status
            return True
        except Exception as e:
            self.errors.append(f"Error during status update: {str(e)}")
            return False
        
    """CHECK THE NUMBERING SERIES IS EXIST"""
    def validate_numbering(self) ->bool:
        try:
            #Only for new record
            if not self.kwargs.get("id"):
                conditions = {'resource': 'Payment Voucher', 'default': True}
                numbering_series = NumberingSeries.objects.filter(**conditions).first()
                
                if not numbering_series:
                    self.errors.append("No matching NumberingSeries found.")
                    return False
            
            return True
        except Exception as e:
            self.errors.append(f"Error during numbering series validation: {str(e)}")
            return False
    
    """VALIDATE THE IMPORTEN FIELDS"""
    def validate_required_fields(self) ->bool:
        supplier_id = []
        employee_ids = []
        account_ids = []

        for field in ['date', 'pay_by', 'pay_mode']:
            if self.kwargs.get(field) is None:
                self.errors.append(f"{field} is required.")
        
        # Exactly ONE must be True
        ai = self.kwargs.get("against_invoice")
        adv = self.kwargs.get("advance")

        if self.kwargs.get('pay_by') == "Supplier & Customer":
            if not (ai or adv):
                self.errors.append("Choose either Against Invoice OR Advance.")
            
            if not self.kwargs.get("currency") :
                self.errors.append(f"currency is required.")
        
        elif self.kwargs.get('pay_by') == "Employee":
            self.kwargs['currency'] = company_info().currency.id if company_info() else None

            if not self.kwargs['currency']:
                self.errors.append(f"currency not found in company master.")

        for payment_voucher_line in self.kwargs.get("payment_voucher_line"):
                # Amount check (safe)
                amount = payment_voucher_line.get("amount")
                if amount is None or amount <= 0:
                    self.errors.append(
                        f"{payment_voucher_line.get('account_name') or payment_voucher_line.get('employee_name') or payment_voucher_line.get('cus_sup_name')} amount is required."
                    )
                    
                # Pay-by rules
                if self.kwargs.get('pay_by') == "Supplier & Customer":
                    for field in ['cus_sup_name','cus_sup']:
                        if not payment_voucher_line.get(field):
                            self.errors.append(f"{field} is required.")
                            continue

                    if payment_voucher_line.get('cus_sup') in supplier_id:
                        self.errors.append(f"{payment_voucher_line.get('cus_sup_name')} Check supplier is duplicate is existed.")
                        continue

                    supplier_id.append(payment_voucher_line.get('cus_sup'))
                    
                    if ai and not payment_voucher_line.get("against_invoice_details"):
                        self.errors.append("Against Invoice details missing.")

                    if adv and not payment_voucher_line.get("advance_details"):
                        self.errors.append("Advance details missing.")

                elif self.kwargs.get('pay_by') == "Employee":
                    for field in ['employee_name','employee','pay_for']:
                        if not payment_voucher_line.get(field):
                            self.errors.append(f"{field} is required.")
                            continue

                    if payment_voucher_line.get('employee') in employee_ids:
                        self.errors.append(f"{payment_voucher_line.get('employee_name')} Check employee is duplicate is existed.")
                        continue
                    employee_ids.append(payment_voucher_line.get('employee'))
                
                else:
                    for field in ['account_name','account']:
                        if not payment_voucher_line.get(field):
                            self.errors.append(f"{field} is required.")
                            continue
                    
                    if payment_voucher_line.get('account') in account_ids:
                        self.errors.append(f"{payment_voucher_line.get('account')} Check account is duplicate is existed.")
                        continue
                    account_ids.append(payment_voucher_line.get('account'))

        # Mode rules
        if self.kwargs.get('pay_mode') == "Bank":
            for bank_field in ['bank', "transfer_via", "chq_ref_no", "chq_date"]:
                if not self.kwargs.get(bank_field):
                    self.errors.append(f"{bank_field} is required.")

        if self.kwargs.get('pay_mode') == "Cash":
            for cash_field in ['bank']:
                if not self.kwargs.get(cash_field):
                    self.errors.append(f"choose case is required.")
        
        if self.kwargs.get('expense_request_id'):
            if self.kwargs.get('pay_by') != "Employee":
                self.errors.append("“You created a payment voucher from an expense request, so only Employee type is allowed.”")
            expence_request = ExpenseRequest.objects.filter(id=self.kwargs.get('expense_request_id')).get()
            if not expence_request:
                self.errors.append("Expence request is not found.")
            if self.kwargs.get('amount') != (expence_request.request_amount or 0):
                self.errors.append("Employee amount and expence request amount is mismatch.")
        
        return len(self.errors) == 0
    
    """VALIDATE THE AGAINST INVOICE"""
    def validate_against_invoice(self, payment_voucher_line, index) ->bool:
        try:
            invoices = payment_voucher_line.get("against_invoice_details")
            instance_list = []
            item_labels = []

            for inv in invoices:
                # Basic required fields
                for inv_field in [ "purchase_invoice_no", 'purchase_invoice', 'adjusted']:
                    if inv.get(inv_field) is None:
                        self.errors.append(f"{inv.get('purchase_invoice') or inv.get('purchase_invoice_no')}-{inv_field} is required.")
                        continue

                # Invoice lookup
                pi = PurchaseInvoice.objects.filter(id=inv.get("purchase_invoice")).first()
                if not pi:
                    self.errors.append(f"{inv.get('purchase_invoice_no')} Purchase Invoice not Found.")
                    continue

                self.purchase_invoice.append(pi)
                item_labels.append(pi.purchase_invoice_no.linked_model_id)
                
                instance = None
                if inv.get("id"):
                    instance = PaymentVoucherAgainstInvoice.objects.filter(id=inv.get("id")).first()
                    
                instance_list.append(instance) 
                
    
            total_invoice_amount = sum((Decimal(inv_.get("adjusted")) or 0) for inv_ in invoices)

            if total_invoice_amount != self.kwargs.get('amount'):
                self.errors.append("Invoice total amount and Supplier Amount is mismatch.")

            if self.errors:
                return False
            
            # Validate with serializer helper
            item_result = validate_common_data_and_send_with_instance(
                    invoices,
                    instance_list,
                    PaymentVoucherAgainstInvoiceSerializer,
                    item_labels,
                    self.info.context)
            
            if item_result.get("error"):
                self.errors.extend(item_result["error"])
                return False
            
            self.against_invoice_details_serializer[index] = item_result.get("instance")

            return True
        except Exception as e:
            self.errors.append(f"Error during against-invoice validation: {str(e)}")
            return False
    
    """VALIDATE THE ADVANCE DETAILS"""
    def validate_advance_details(self, payment_voucher_line, index) ->bool:

        try:
            advances = payment_voucher_line.get("advance_details")
            updated_advance = []
            instance_list = []
            item_labels = []
            
            for adv  in advances:
                for adv_field in ['adv_remark', "amount"]:
                    if adv.get(adv_field) is None:
                        self.errors.append(f"{adv.get('adv_remark')}-{adv_field} is required.")
                        continue
                item_labels.append(adv.get("adv_remark"))

                instance = None
                adv['remaining'] = adv.get("amount")

                if adv.get("id"):
                    instance = PaymentVoucherAdvanceDetails.objects.filter(id=adv.get("id")).first()
                    adv['remaining'] = instance.get("remaining")

                updated_advance.append(adv)
                    
                instance_list.append(instance)

            total_advance_amount = sum((adv_.get("amount") or 0) for adv_ in advances)
            if total_advance_amount != self.kwargs.get('amount'):
                self.errors.append("Advance total amount and  Customer Amount is mismatch.")
                

            if self.errors:
                return False
            
            item_result = validate_common_data_and_send_with_instance(
                    updated_advance,
                    instance_list,
                    PaymentVoucherAdvanceDetailsSerializer,
                    item_labels,
                    self.info.context)
            
            if item_result.get("error"):
                self.errors.extend(item_result["error"])
                return False

            self.advance_details_serializer[index] = item_result.get("instance")
            return True
            
        except Exception as e:
            self.errors.append(f"An exception occurred while validate advance details: {str(e)}")
            return False
    
    """VALIDATE THE PV LINE"""
    def validate_pv_line(self) ->bool:
        try:
            payment_voucher_line = self.kwargs.get("payment_voucher_line")
            instance_list = []
            item_labels = []

            for index, payment_voucher_line in enumerate(payment_voucher_line):
                if self.kwargs.get('pay_by') == "Supplier & Customer":
                    if payment_voucher_line.get("advance_details"):
                        if not self.validate_advance_details(payment_voucher_line, index):
                            continue
                    else:
                        if not self.validate_against_invoice(payment_voucher_line, index):
                            continue
                
                item_labels.append(
                                    payment_voucher_line.get('account_name')
                                    or payment_voucher_line.get('employee_name')
                                    or payment_voucher_line.get('cus_sup_name')
                                )

                instance = None
                if payment_voucher_line.get("id"):
                    instance = PaymentVoucherLine.objects.filter(id=payment_voucher_line.get("id")).first()
                
                instance_list.append(instance)

            # Validate with serializer helper
            item_result = validate_common_data_and_send_with_instance(
                    payment_voucher_line,
                    instance_list,
                    PaymentVoucherLineSerializer,
                    item_labels,
                    self.info.context)
            
            if item_result.get("error"):
                self.errors.extend(item_result["error"])
                return False
            
            self.payment_voucher_line_serializer.extend(item_result.get("instance"))
            return True
            
        except Exception as e:
            self.errors.append(f"An exception occurred while validate supplier: {str(e)}")
            return False
    
    """Save pv line"""
    def save_pv_line(self) ->bool:
        try:
            for index , payment_voucher_line_serializer in enumerate(self.payment_voucher_line_serializer):
                payment_voucher_line_serializer.save()
                
                if index in self.advance_details_serializer:
                    for advance_detail_serializer in self.advance_details_serializer[index]:
                        advance_detail_serializer.save(payment_voucher_line=payment_voucher_line_serializer.instance)
                
                if index in self.against_invoice_details_serializer:
                    for against_invoice_detail_serializer in self.against_invoice_details_serializer[index]:
                        against_invoice_detail_serializer.save(payment_voucher_line=payment_voucher_line_serializer.instance)

                self.payment_voucher_line_instance.append(payment_voucher_line_serializer.instance)
                return True
        except Exception as e:
            self.errors.append(f"An exception occurred while receipt voucher line: {str(e)}")
            transaction.set_rollback(False)
            return False

    """SAVE THE PAYMENT VOUCHER"""
    def save_payment_voucher(self) ->bool:
        try:
            serializer_class = PaymentVoucherSerializer
            if self.payment_voucher:
                serializer = serializer_class(self.payment_voucher,
                                            data=self.kwargs,
                                            partial=True,
                                            context={'request': self.info.context})
            else:
                serializer = serializer_class(data=self.kwargs,
                                            context={'request': self.info.context})

            if not serializer.is_valid():
                self.errors.extend(f"{field} → {', '.join(map(str, messages))}"
                    for field, messages in serializer.errors.items())
                return False

            serializer.save()
            self.payment_voucher = serializer.instance

            # Link children
            for payment_voucher_line_instance in self.payment_voucher_line_instance:
                payment_voucher_line_instance.payment_voucher = self.payment_voucher
                payment_voucher_line_instance.save()
            
          
            

            # deleteCommanLinkedTable([item.id for item in self.old_advance_details_instance],
            #                         [item.id for item in self.advance_details_instance],
            #                         PaymentVoucherAdvanceDetails)
            # deleteCommanLinkedTable([charge.id for charge in self.old_against_invoice_details_instance],
            #                         [charge.id for charge in self.against_invoice_details_instance],
            #                         PaymentVoucherAgainstInvoice)
            return True
        
        except Exception as e:
            self.errors.append(f"Error saving payment voucher: {str(e)}")
            return False

    """SAVE THE PURCHACE PAID INVOICE ON SUBMIT"""
    def save_purchase_paid_detail(self) -> bool:
        purchase_paid_details = []
        validation_errors = []
        try:
            for pv_line in self.kwargs.get("payment_voucher_line"):
                for aid in pv_line.get("against_invoice_details", []):
                    data = {
                        "purchase_invoice": aid.get("sales_invoice"),
                        "payment_voucher": self.payment_voucher.id,
                        "amount": aid.get("adjusted"),
                    }
                    serializer = PurchasePaidDetailsSerializer(
                        data=data,
                        context={'request': self.info.context} if self.info.context else {}
                    )
                    if serializer.is_valid():
                        purchase_paid_details.append(serializer)
                    else:
                        for field, errors in serializer.errors.items():
                            for msg in errors:
                                validation_errors.append(f"{aid.get('sales_invoice')} - {field}: {msg}")
            # If any validation errors, stop the whole thing
            if validation_errors:
                self.errors.extend(validation_errors)
                transaction.set_rollback(False)
                return False

            # Everything valid → now save
            for ppd in purchase_paid_details:
                ppd.save()

        except Exception as e:
            self.errors.append(f"Error saving paid details: {str(e)}")
            transaction.set_rollback(False)
            return False

    def response(self) -> dict:
        return {
            "payment_voucher": self.payment_voucher,
            "success": self.success,
            "errors": [",\n ".join(self.errors)] if self.errors else None,
        }
    


def payment_voucher_genral_update(data):
    valid_serializers = []
    errors = []
    credits = data.get("credits", {})
    debit = data.get("debit", [])

    credits_amount = Decimal("0.00")
    REQUIRED_FIELDS = ["date", "voucher_type", "payment_voucher_no", "account", "created_by"]

    # Process credit
    for idx, credit in enumerate(credits):
        for field in REQUIRED_FIELDS + ["credit"]:
            if credit.get(field) in [None, ""]:
                errors.append(f"credit [{idx}] → '{field}' is required.")
        
        credits_amount += credit.get("credit", 0)
        serializer = AccountsGeneralLedgerSerializer(data=credit)
        if not serializer.is_valid():
            for field, error in serializer.errors.items():
                errors.append(f"credit [{idx}] → {field}: {'; '.join(map(str, error))}")
        else:
            valid_serializers.append(serializer)

    # Process debit
    for field in REQUIRED_FIELDS + ["debit"]:
        if debit.get(field) in [None, ""]:
            errors.append(f"debit → '{field}' is required.")

    serializer = AccountsGeneralLedgerSerializer(data=debit)
    if not serializer.is_valid():
        for field, error in serializer.errors.items():
            errors.append(f"debit → {field}: {'; '.join(map(str, error))}")
    else:
        valid_serializers.append(serializer)

    # Compare debit and credit amounts
    debit_amount = Decimal(str(debit.get("debit", 0)))
    if credits_amount != debit_amount:
        errors.append(f"Debit amount ({debit_amount}) and credit amount ({credits_amount}) do not match.----")

    # Return errors if any
    if errors:
        return {"success": False, "errors": errors}

    # Save all valid serializers
    for valid_serializer in valid_serializers:
        valid_serializer.save()

    return {"success": True, "errors": []}