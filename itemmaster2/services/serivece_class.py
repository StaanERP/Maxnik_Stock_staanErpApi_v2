from itemmaster2.models import *
from itemmaster2.Serializer import *
# from itemmaster2.Utils.CommanUtils import *
# from itemmaster.schema import *
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
from decimal import Decimal, InvalidOperation

class ReceiptVoucherService:

    def __init__(self, kwargs, status, info):
        self.kwargs = kwargs
        self.status_text = status
        self.status = status
        self.info = info
        
        self.receipt_voucher = None
        self.against_invoice_details_serializer = {}
        self.advance_details_serializer = {}
        self.receipt_voucher_line_serializer = []

        self.against_invoice_details_instance = {}
        self.advance_details_instance = {}
        self.receipt_voucher_line_instance = []
        self.old_against_invoice_details_instance = []
        self.old_advance_details_instance = []

        self.success = False
        self.errors = []
    
    """MAIN CONTROLLER"""
    def process(self) -> dict:
        with transaction.atomic():
            try:
                if self.status_text in ["Draft", 'Submit']:
                    
                    if not self.get_receipt_voucher(): return self.response()
                    print("----1")
                    if not self.validate_required_fields(): return self.response()
                    print("----2")
                    if not self.validate_numbering(): return self.response()
                    print("----3")
                    if not self.update_status_instance(): return self.response()
                    print("----4")
                    # Child validations
                    if not self.validate_rv_line(): return self.response()
                    print("----5")
                    if not self.save_rv_line(): return self.response()
                    print("----6")
                    # Save main voucher
                    if not self.save_receipt_voucher(): return self.response()
                    print("----4")
                    if self.status_text == "Submit":
                        if not self.save_sales_paid_detail(): return self.response()
                            

                    self.success = True
                    return self.response()
                else:
                    self.errors.append(f"{self.status_text} Unexpeted status.")
                return self.response()
            
            except Exception as e:
                self.errors.append(f"Unexpected server error: {str(e)}")
                transaction.set_rollback(False)
                return self.response()

    """FETCH MAIN DOCUMENT"""
    def get_receipt_voucher(self) ->bool:
        
        try:
            if "id" in self.kwargs and self.kwargs.get("id"):
                rv = ReceiptVoucher.objects.filter(id=self.kwargs.get("id")).first()

                if not rv:
                    self.errors.append("Receipt Voucher not found.")
                    return False
                
                # State protection rules
                current = rv.status.name

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

                # self.old_advance_details_instance = rv.receiptvoucheradvancedetails_set.all()
                # self.old_against_invoice_details_instance = rv.receiptvoucheragainstinvoice_set.all()

                self.receipt_voucher = rv
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
                name=self.status_text, table="Receipt Voucher"
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
                conditions = {'resource': 'Receipt Voucher', 'default': True}
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

        try:
            for field in ['rv_date', 'pay_by', 'pay_mode']:
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

            
            for receipt_voucher_line in self.kwargs.get("receipt_voucher_lines"):
                # Amount check (safe)
                amount = receipt_voucher_line.get("amount")
                if amount is None or amount <= 0:
                    self.errors.append(
                        f"{receipt_voucher_line.get('account_name') or receipt_voucher_line.get('employee_name') or receipt_voucher_line.get('cus_sup_name')} amount is required."
                    )
                    
                # Pay-by rules
                if self.kwargs.get('pay_by') == "Supplier & Customer":
                    for field in ['cus_sup_name','cus_sup']:
                        if not receipt_voucher_line.get(field):
                            self.errors.append(f"{field} is required.")
                            continue

                    if receipt_voucher_line.get('cus_sup') in supplier_id:
                        self.errors.append(f"{receipt_voucher_line.get('cus_sup_name')} Check supplier is duplicate is existed.")
                        continue

                    supplier_id.append(receipt_voucher_line.get('cus_sup'))
                    
                    if ai and not receipt_voucher_line.get("against_invoice_details"):
                        self.errors.append("Against Invoice details missing.")

                    if adv and not receipt_voucher_line.get("advance_details"):
                        self.errors.append("Advance details missing.")

                elif self.kwargs.get('pay_by') == "Employee":
                    for field in ['employee_name','employee','pay_for']:
                        if not receipt_voucher_line.get(field):
                            self.errors.append(f"{field} is required.")
                            continue

                    if receipt_voucher_line.get('employee') in employee_ids:
                        self.errors.append(f"{receipt_voucher_line.get('employee_name')} Check employee is duplicate is existed.")
                        continue
                    employee_ids.append(receipt_voucher_line.get('employee'))
                
                else:
                    for field in ['account_name','account']:
                        if not receipt_voucher_line.get(field):
                            self.errors.append(f"{field} is required.")
                            continue
                    
                    if receipt_voucher_line.get('account') in account_ids:
                        self.errors.append(f"{receipt_voucher_line.get('account')} Check account is duplicate is existed.")
                        continue
                    account_ids.append(receipt_voucher_line.get('account'))

            # Mode rules
            if self.kwargs.get('pay_mode') == "Bank":
                for bank_field in ['bank', "transfer_via", "chq_ref_no", "chq_date"]:
                    if not self.kwargs.get(bank_field):
                        self.errors.append(f"{bank_field} is required.")

            if self.kwargs.get('pay_mode') == "Cash":
                if not self.kwargs.get('bank'):
                    self.errors.append(f"choose cash is required.")
            
            return len(self.errors) == 0
        
        except Exception as e:
            self.errors.append(f"Error during required fields validation: {str(e)}")
            return False

    def validate_rv_line(self) ->bool:
        try:
            receipt_voucher_lines = self.kwargs.get("receipt_voucher_lines")
            instance_list = []
            item_labels = []

            for index, receipt_voucher_line in enumerate(receipt_voucher_lines):
                if self.kwargs.get('pay_by') == "Supplier & Customer":
                    if receipt_voucher_line.get("advance_details"):
                        if not self.validate_advance_details(receipt_voucher_line, index):
                            continue
                    else:
                        if not self.validate_against_invoice(receipt_voucher_line, index):
                            continue
                item_labels.append(
                                    receipt_voucher_line.get('account_name')
                                    or receipt_voucher_line.get('employee_name')
                                    or receipt_voucher_line.get('cus_sup_name')
                                )

                instance = None
                if receipt_voucher_line.get("id"):
                    instance = ReceiptVoucherLine.objects.filter(id=receipt_voucher_line.get("id")).first()
                
                instance_list.append(instance)

            # Validate with serializer helper
            item_result = validate_common_data_and_send_with_instance(
                    receipt_voucher_lines,
                    instance_list,
                    ReceiptVoucherLineSerializer,
                    item_labels,
                    self.info.context)
            print(item_result)
            if item_result.get("error"):
                self.errors.extend(item_result["error"])
                return False
            
            self.receipt_voucher_line_serializer.extend(item_result.get("instance"))
            return True
            
        except Exception as e:
            self.errors.append(f"An exception occurred while validate supplier: {str(e)}")
            return False
        
    def save_rv_line(self) ->bool:
        try:
            print(self.receipt_voucher_line_serializer)
            for index , receipt_voucher_line_serializer in enumerate(self.receipt_voucher_line_serializer):
                print(index)
                receipt_voucher_line_serializer.save()
                
                if index in self.advance_details_serializer:
                    for advance_detail_serializer in self.advance_details_serializer[index]:
                        advance_detail_serializer.save(receipt_voucher_line=receipt_voucher_line_serializer.instance)
                
                if index in self.against_invoice_details_serializer:
                    for against_invoice_detail_serializer in self.against_invoice_details_serializer[index]:
                        against_invoice_detail_serializer.save(receipt_voucher_line=receipt_voucher_line_serializer.instance)
                print(receipt_voucher_line_serializer.instance)
                self.receipt_voucher_line_instance.append(receipt_voucher_line_serializer.instance)
            return True
        except Exception as e:
            self.errors.append(f"An exception occurred while receipt voucher line: {str(e)}")
            transaction.set_rollback(False)
            return False
        
    """VALIDATE THE AGAINST INVOICE"""
    def validate_against_invoice(self, receipt_voucher_line, index) ->bool:
        try:
            invoices = receipt_voucher_line.get("against_invoice_details")
            instance_list = []
            item_labels = []
            for inv  in invoices:
                # Basic required fields
                for inv_field in ['salesInvoiceNo', "sales_invoice", 'adjusted']:
                    if inv.get(inv_field) is None:
                        self.errors.append(f"{inv.get('salesInvoiceNo')}- {inv_field} is required.")
                        continue

                # Invoice lookup
                si = SalesInvoice.objects.filter(id=inv.get("sales_invoice")).first()
                if not si:
                    self.errors.append(f"{inv.get('salesInvoiceNo')} Sales invoice not Found.")
                    continue
                lable = si.sales_invoice_no.linked_model_id
                item_labels.append(lable)
                
                if self.status_text == 'Submit':
                    if self.kwargs.get("currency") != si.sales_dc.first().sales_order.currency:
                        self.errors.append("Please check. These invoices use different currencies.")
                        continue

                    # Balance check
                    total_paid = si.salespaiddetails_set\
                    .aggregate(total=Sum("amount"))["total"] or 0

                    net_amount = si.net_amount
                    balance = net_amount - total_paid
                    if (balance - inv.get("amount")) < 0:
                        self.errors.append(
                                f"{inv.get('sales_order_no')} → The adjusted value ({inv.get('amount')}) is higher than the available balance ({balance}). Please verify the balance before adjusting."
                        )
                
                instance = None
                if inv.get("id"):
                    instance = ReceiptVoucherAgainstInvoice.objects.filter(id=inv.get("id")).first()
                    
                instance_list.append(instance)
            
            total_invoice_amount = sum((inv_.get("adjusted") or 0) for inv_ in invoices)
            
            if total_invoice_amount != receipt_voucher_line.get('amount'):
                self.errors.append("Invoice total amount and Customer Amount is mismatch.")

            if self.errors:
                return False
            
            # Validate with serializer helper
            item_result = validate_common_data_and_send_with_instance(
                    invoices,
                    instance_list,
                    ReceiptVoucherAgainstInvoiceSerializer,
                    item_labels, 
                    self.info.context)
            
            if item_result.get("error"):
                self.errors.extend(item_result["error"])
                return False

            self.against_invoice_details_serializer[index]=item_result.get("instance")
            return True
        
        except Exception as e:
            self.errors.append(f"Error during against-invoice validation: {str(e)}")
            transaction.set_rollback(False)
            return False
    
    """VALIDATE THE ADVANCE DETAILS"""
    def validate_advance_details(self, receipt_voucher_line, index) ->bool:
        advances = receipt_voucher_line.get("advance_details")
        try:
            instance_list = []
            item_labels = []

            for adv in advances:
                for adv_field in ['adv_remark', "amount"]:
                    if adv.get(adv_field) is None:
                        self.errors.append(f"{adv.get('adv_remark')}-{adv_field} is required.")
                        continue

                item_labels.append(adv.get("adv_remark"))

                instance = None
                if adv.get("id"):
                    instance = ReceiptVoucherAdvanceDetails.objects.filter(id=adv.get("id")).first()
                    
                instance_list.append(instance)

            total_advance_amount = sum((adv_.get("amount") or 0) for adv_ in advances)
            if total_advance_amount != receipt_voucher_line.get('amount'):
                self.errors.append("Advance total amount and  Customer Amount is mismatch.")

            if self.errors:
                return False
            
            item_result = validate_common_data_and_send_with_instance(
                    advances,
                    instance_list,
                    ReceiptVoucherAdvanceDetailsSerializer,
                    item_labels,
                    self.info.context)
            
            if item_result.get("error"):
                self.errors.extend(item_result["error"])
                return False
            
            self.advance_details_serializer[index] = item_result.get("instance")
            return True
            
        except Exception as e:
            self.errors.append(f"An exception occurred while validate advance details: {str(e)}")
            transaction.set_rollback(False)
            return False
   
    """SAVE THE RECEIPT VOUCHER"""
    def save_receipt_voucher(self) ->bool:
        try:
            serializer_class = ReceiptVoucherSerializer
            if self.receipt_voucher:
                serializer = serializer_class(self.receipt_voucher, 
                                            data=self.kwargs, 
                                            partial=True, 
                                            context={'request': self.info.context})
            else:
                serializer = serializer_class(data=self.kwargs,
                                            context={'request': self.info.context})
            print(serializer.is_valid())
            if not serializer.is_valid():
                self.errors.extend(f"{field} → {', '.join(map(str, messages))}"
                    for field, messages in serializer.errors.items())
                return False
            print("submit-1")
            serializer.save()
            self.receipt_voucher = serializer.instance
            print("submit-1")
            for receipt_voucher_line_instance in self.receipt_voucher_line_instance:
                receipt_voucher_line_instance.receipt_voucher = serializer.instance
                receipt_voucher_line_instance.save()

            
            
            # deleteCommanLinkedTable([item.id for item in self.old_advance_details_instance],
            #                         [item.id for item in self.advance_details_instance],
            #                         ReceiptVoucherAdvanceDetails)
            # deleteCommanLinkedTable([charge.id for charge in self.old_against_invoice_details_instance],
            #                         [charge.id for charge in self.against_invoice_details_instance],
            #                         ReceiptVoucherAgainstInvoice)
            return True
        
        except Exception as e:
            self.errors.append(f"Error saving receipt voucher: {str(e)}")
            transaction.set_rollback(False)
            return False

    """SAVE THE SALES PAID INVOICE ON SUBMIT"""
    def save_sales_paid_detail(self) ->bool:
        sales_paid_details = []
        validation_errors = []
        try:
            for rv_line in self.kwargs.get("receipt_voucher_lines", []):
                for aid in rv_line.get("against_invoice_details", []):
                    
                    data = {
                        "sales_invoice": aid.get("sales_invoice"),
                        "receipt_voucher": self.receipt_voucher.id,
                        "amount": aid.get("adjusted"),
                    }

                    serializer = SalesPaidDetailsSerializer(
                        data=data,
                        context={'request': self.info.context} if self.info.context else {}
                    )

                    if serializer.is_valid():
                        sales_paid_details.append(serializer)
                        
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
            for spd in sales_paid_details:
                spd.save()

            return True

        except Exception as e:
            self.errors.append(f"Error saving paid details: {str(e)}")
            transaction.set_rollback(False)
            return False

    def response(self) -> dict:
        return {
            "receipt_voucher": self.receipt_voucher,
            "success": self.success,
            "errors": [",\n ".join(self.errors)] if self.errors else None,
        }


def receipt_voucher_genral_update(data):
    valid_serializers = []
    errors = []
    credits = data.get("credits", {})
    debit = data.get("debit", [])

    credits_amount = Decimal("0.00")
    REQUIRED_FIELDS = ["date", "voucher_type", "receipt_voucher_voucher_no", "account", "created_by"]

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


class CreditNoteService:

    def __init__(self, kwargs, status, info):
        self.status_text= status
        self.kwargs = kwargs
        self.info = info

        self.credit_note = None
        self.item_details_serializer = []
        self.item_combo_serializer = {}
        self.other_income_serializer = []
        self.account_serializer = []
        self.new_item_details_instances = []
        self.new_other_income_instances = []
        self.new_account = []
        self.old_item_details_instances = []
        self.old_other_income_instances = []
        self.old_account = []
        self.gst_transaction = None
        self.tcs = None
        self.tds = None
        self.gst_transaction = None
        self.updated_item_details = None
        self.updated_other_income = None
    
        self.status = None
        self.success = False
        self.errors = []
    
    # Get or validate existing credit note
    def get_credit_note(self)-> bool:
        credit_id = self.kwargs.get("id")
        if credit_id:
            self.credit_note =  CreditNote.objects.filter(id=credit_id).first()
            if not self.credit_note:
                self.errors.append("Credit note not found.")
                return False
            
            self.old_item_details_instances.extend(self.credit_note.creditnoteitemdetails_set.all())
            self.old_other_income_instances.extend(self.credit_note.creditnoteotherincomecharges_set.all())
            self.old_account.extend(self.credit_note.creditnoteaccount_set.all())

            if self.status_text == "Draft" and self.credit_note.status.name in ['Submit', "Canceled"]:
                self.errors.append(f"Already {self.credit_note.status.name} Credit Note did'n make Draft again.")
            elif self.status_text == "Submit" and self.credit_note.status.name in ["Canceled","Submit" ]:
                self.errors.append(f"Already {self.credit_note.status.name} Credit Note did'n make Submit again.")

            buyer = self.credit_note.buyer
            if buyer.tds and "P" in buyer.pan_no:
                self.tds =  "P"
            elif buyer.tds and "P" not in buyer.pan_no:
                self.tds = "O"
            if buyer.tcs in ['PURCHASE', "BOTH"]:
                if buyer.pan_no and "P" in buyer.pan_no:
                    self.tcs =  "WP"
                elif buyer.pan_no and "P" not in buyer.pan_no:
                    self.tcs =  "WO"
                else:
                    self.tcs =  "WOO"
        
        sales_return_id = bool(self.kwargs.get("sales_return"))
        is_have_sales_return_id = any(item.get("sales_return_item") for item in self.kwargs.get("item_details"))

        if sales_return_id and not is_have_sales_return_id:
            self.errors.append("Sales return invoice item id is missing in item details.")
        
        if not sales_return_id and is_have_sales_return_id:
            self.errors.append("Sales return invoice id is missing.")

        if not self.kwargs.get('item_details', []) and not self.kwargs.get('accounts', []):
            self.errors.append("At least one item detail or account is required.")
            return False

        if len(self.errors):
            return False
        
        return True

    # Validate mandatory fields
    def validate_required_fields(self)-> bool:
        REQUIRED_FIELDS = [
            "status", "cn_date", "sales_person", "currency","exchange_rate",
            "department", "gst_nature_type", "gst_nature_transaction",
            "buyer", "buyer_address", "buyer_contact_person", "buyer_gstin_type",
            "buyer_gstin", "buyer_state", "buyer_place_of_supply", 
            "consignee", "consignee_address", "consignee_contact_person",
            "consignee_gstin_type", "consignee_gstin", "consignee_state",
            "consignee_place_of_supply", "terms_conditions", "terms_conditions_text",
            "item_total_befor_tax", "taxable_value", 'net_amount']
        
        for field in REQUIRED_FIELDS:
            if self.kwargs.get(field) is None:
                self.errors.append(f'{field} is required.')

        return not self.errors

    # Validate and fetch status instance
    def update_status_instance(self)-> bool:
        self.status  = CommanStatus.objects.filter(name=self.status_text, table="Credit Note").first()
        
        if not self.status :
            self.errors.append(f"Ask developer to add status '{self.status_text}' in CommanStatus.")
            return False
        
        self.kwargs["status"] = self.status.id
        return True
    
    # Validate numbering series
    def validate_numbering(self)-> bool:
        credit_note_id = self.kwargs.get("id")
        if not credit_note_id:
            conditions = {'resource': 'Credit Note', 'default': True, "department": self.kwargs.get("department")}
            numbering_series = NumberingSeries.objects.filter(**conditions).first()
            if not numbering_series:
                self.errors.append("No matching NumberingSeries found.")
                return False
        return True
    
     # validate Combo item
    
    def validate_item_combo(self, combo_items, parent_index, parent_item_master)->bool:
        try:
            instance_list = []
            item_labels = []

            for combo_item in combo_items:
                sales_return_combo_item = combo_item.get("sales_return_combo_item")

                item_master  = ItemMaster.objects.filter(id=combo_item.get("itemmaster")).first()
                if not item_master :
                    self.errors.append(f"{parent_item_master}-->{combo_item.get('itemmaster')} not found in Item Master.")
                    continue
                
                if sales_return_combo_item:
                    sr_item_combo  = SalesReturnItemCombo.objects.filter(id=sales_return_combo_item).first()
                    if not sr_item_combo :
                        self.errors.append(f"{parent_item_master}-->{item_master} -> sales return challan item combo not found .")
                        continue

                item_labels.append(str(item_master))

                for field in ["itemmaster", "uom", "qty", "rate", "amount"]:
                    if combo_item.get(field) is None:
                        self.errors.append(f'{item_master} → {field} is required.')
                
                if self.errors:
                    return False
                
                instance = None
                if combo_item.get('id'):
                    instance = CreditNoteComboItemDetails.objects.filter(id=combo_item.get("id")).first()

                    if not instance:
                        self.errors.append(f'{parent_item_master}-->{item_master} → Credit Note Item combo instance not Found.')
                        continue
                
                instance_list.append(instance)

            if self.errors:
                return False
            
            item_result = validate_common_data_and_send_with_instance(
                combo_items, instance_list,
                CreditNoteComboItemDetailsSerializer,
                item_labels,
                self.info.context)
            
            if item_result.get("error"):
                self.errors.extend(item_result.get("error"))
                return False
            
            self.item_combo_serializer.update({parent_index:item_result.get("instance")})
            return True
        
        except Exception as e:
            self.errors.append(f"An exception occurred {str(e)}")
            return False
        
    # Validate item details
    def validate_item_details(self)-> bool:
        instance_list = []
        item_details = self.kwargs.get('item_details', [])
        item_labels = []

        if not item_details:
            return True

        for index, item in enumerate(item_details):
            sales_return_item_id = item.get("sales_return_item")
            item_master  = ItemMaster.objects.filter(id=item.get("itemmaster")).first()
            if not item_master :
                self.errors.append(f"{item.get('description')} not found in Item Master.")
                return False
            
            if sales_return_item_id:
                sr_item  = SalesReturnItemDetails.objects.filter(id=sales_return_item_id).first()
                if not sr_item :
                    self.errors.append(f"{item_master} -> sales return challan item not found .")
            item_labels.append(str(item_master))
            
            for field in ["index", "itemmaster","description",  "qty", "uom",  "rate", "amount"]:
                if item.get(field) is None:
                    self.errors.append(f'{item_master} → {field} is required.')

            
            if item_master.item_combo_bool:
                if not item.get("combo_details"):
                    self.errors.append(f"{item_master}-> item combo not found.")
                    continue

                if not self.validate_item_combo(item.get("combo_details"), index, item_master):
                    continue

            item['combo_details'] = []
            instance = None
            if item.get('id'):
                instance = CreditNoteItemDetails.objects.filter(id=item.get("id")).first()

                if not instance:
                    self.errors.append(f'{item_master} → Credit Note Item instance not Found.')
                
            instance_list.append(instance)
        
        if self.errors:
            return False
        
        item_result = validate_common_data_and_send_with_instance(
            item_details, instance_list,
            CreditNoteItemDetailsSerializer,
            item_labels,
            self.info.context
        )
        
        if item_result.get("error"):
            self.errors.extend(item_result["error"])
            return False
        
        self.item_details_serializer.extend(item_result.get("instance"))
        return True
    
    # Validate other charges
    def validate_other_charges(self)-> bool:
        instance_list = []
        other_income_charges = self.kwargs.get('other_income_charge', [])
        item_labels = []

        if not other_income_charges:
            return True
        
        for charge  in other_income_charges:
            other_income_id = charge .get("other_income_charges")
            other_income_charge = OtherIncomeCharges.objects.filter(id=other_income_id).first()
            
            if not other_income_charge:
                self.errors.append(f"{other_income_id} other income charges id is not found.")
                continue
            item_labels.append(other_income_charge)

            for field in ["other_income_charges", "amount"]:
                if charge.get(field) is None:
                    self.errors.append(f'{other_income_charge} → {field} is required.')

            instance = None
            if charge.get('id'):
                instance = CreditNoteOtherIncomeCharges.objects.filter(id=charge.get("id")).first()
                if not instance:
                    self.errors.append(f'{other_income_charge} → credit note other income charge {charge.get("id")} not Found.')
                
            instance_list.append(instance)
        
        if self.errors:
            return False
        
        item_result = validate_common_data_and_send_with_instance(
                            other_income_charges, instance_list,
                            CreditNoteOtherIncomeChargesSerializer,
                            item_labels,
                            self.info.context)
        
        if item_result.get("error"):
            self.errors.extend(item_result["error"])
            return False
        
        self.other_income_serializer.extend(item_result.get("instance"))
        return True
    
    # Validate account
    def validate_account(self)-> bool:
        instance_list = []
        accounts = self.kwargs.get('accounts', [])
        item_labels = []
        
        if not accounts:
            return True

        for account in accounts:
            credit_note_acount_id = account.get("id")
            account_master_instance = AccountsMaster.objects.filter(id=account.get("account_master")).first()

            if not account_master_instance :
                self.errors.append(f"{account.get('account_master')} not found in Account Master.")
                continue
            
            item_labels.append(str(account_master_instance.accounts_name))

            for field in ["account_master",   "amount"]:
                if account.get(field) is None:
                    self.errors.append(f'{account_master_instance} → {field} is required.')
            
            instance = None
            if credit_note_acount_id:
                instance = CreditNoteAccount.objects.filter(id=credit_note_acount_id).first()

                if not instance:
                    self.errors.append(f'{account_master_instance.accounts_name} → Account instance not Found.')
                
            instance_list.append(instance)
            
        if self.errors:
            return False
            
        item_result = validate_common_data_and_send_with_instance(
            accounts, instance_list,
            CreditNoteAccountSerializer,
            item_labels,
            self.info.context)
        
        if item_result.get("error"):
            self.errors.extend(item_result["error"])
            return False
        
        self.account_serializer.extend(item_result.get("instance"))
        return True
    
    def save_combo(self, parent_index, parent_instance)->bool:
        if parent_index in self.item_combo_serializer:
            for combo in self.item_combo_serializer[parent_index]:
                vd = combo.validated_data
                vd["credit_note_item"] = parent_instance
                combo.save(**vd)

    # Save item details
    def save_item_details(self)-> bool:
        if not self.item_details_serializer:
            return True
        try: 
            for index, serializer_item in enumerate(self.item_details_serializer):
                if serializer_item:
                    serializer_item.save()
                    print("serializer_item.instance", index, serializer_item.instance)
                    self.save_combo(index, serializer_item.instance)
                    self.new_item_details_instances.append(serializer_item.instance)
            return True

        except Exception as e:
            print("e", e)
            self.errors.append(f"An exception occurred while saving item details: {str(e)}")
            return False

    # Save other income charges
    def save_other_income_charges(self)-> bool:
        if not self.other_income_serializer:
            return True
        
        try:
            for serializer_other_income in self.other_income_serializer:
                if serializer_other_income:
                    serializer_other_income.save()
                    self.new_other_income_instances.append(serializer_other_income.instance)
            return True
        except Exception as e:
            self.errors.append(f"An exception occurred while saving other income: {str(e)}")
            return False
    
    def save_account(self)-> bool:
        if not self.account_serializer:
            return True
        
        try:
            for serializer_account in self.account_serializer:
                if serializer_account:
                    serializer_account.save()
                    self.new_account.append(serializer_account.instance)
            return True
        
        except Exception as e:
            self.errors.append(f"An exception occurred while saving account : {str(e)}")
            return False

    # Save credit note
    def save_credit_note(self)-> bool:
        try:
            serializer_class = CreditNoteSerializer
            if self.credit_note:
                serializer = serializer_class(self.credit_note, data=self.kwargs, partial=True, context={'request': self.info.context})
            else:
                serializer = serializer_class(data=self.kwargs, context={'request': self.info.context})

            if not serializer.is_valid():
                self.errors.extend(f"{field} → {', '.join(map(str, messages))}"
                    for field, messages in serializer.errors.items())
                return False

            serializer.save()
            self.credit_note = serializer.instance

            for item in self.new_item_details_instances:
                item.credit_note = self.credit_note
                item.save()

            for income in self.new_other_income_instances:
                income.credit_note = self.credit_note
                income.save()
            
            for account in self.new_account:
                account.credit_note = self.credit_note
                account.save()
            
            deleteCommanLinkedTable([item.id for item in self.old_item_details_instances],  [item.id for item in self.new_item_details_instances], DebitNoteItemDetail)
            deleteCommanLinkedTable([charge.id for charge in self.old_other_income_instances], [charge.id for charge in self.new_other_income_instances], DebitNoteOtherIncomeCharge)
            deleteCommanLinkedTable([account.id for account in self.old_account], [acount.id for acount in self.new_account], DebitNoteAccount)
            return True
        except Exception as e:
            self.errors.append(f"Error saving Credit Note: {str(e)}")
            return False
    
    # validate item details on submit
    def validate_item_detail_on_submit(self)->bool:
        if self.credit_note and not self.credit_note.sales_return:
            return True
        
        for item in self.old_item_details_instances:
            sales_return_item = item.sales_return_item
            item_master = item.item_master
            lable = f"{item_master.item_part_code}-{item_master.item_name}"

            if not sales_return_item:
                self.errors.append(f"{lable} Sales return item is missing.")
                continue
            
            sales_invoice_item = sales_return_item.sales_invoice_item_detail
            if not sales_invoice_item:
                self.errors.append(f"{lable} sales invoice item is missing.")
                continue

            if item_master.item_combo_bool:
                for combo_item in item.creditnotecomboitemdetails_set.all():
                    sales_return_combo_item = combo_item.sales_return_combo_item.sales_invoice_item_combo
                    if not sales_return_combo_item:
                        self.errors.append(f"{lable}-->{combo_item.itemmaster} Sales return item combo is missing.")
                    
                    if (sales_return_combo_item.rate or 0) != (combo_item.rate or 0):
                        self.errors.append(f"{lable}-->{combo_item.itemmaster}   Rate is mismatch with sales invoice.")

                    if (sales_return_combo_item.qty or 0) != (combo_item.qty or 0):
                        self.errors.append(f"{lable}-->{combo_item.itemmaster}  QTY is mismatch with sales return.")

            if sales_invoice_item.rate != item.rate:
                self.errors.append(f"{lable}   Rate is mismatch with sales invoice.")
            if sales_return_item.qty != item.qty:
                self.errors.append(f"{lable}  QTY is mismatch with sales return.")
        return not self.errors
    
    def to_decimal(self, value):
        """Safely convert strings/numbers to Decimal for accurate comparison."""
        if value is None:
            return Decimal('0')
        try:
            return Decimal(str(value)).quantize(Decimal('0.000'))
        except (InvalidOperation, TypeError):
            return Decimal('0')
    # validate tax flow
    def validate_tax(self)->bool:
        if self.credit_note and self.credit_note.sales_return:
            return True
        
        self.gst_transaction = self.credit_note.gst_nature_transaction

        if self.old_item_details_instances:
            for item in self.old_item_details_instances:
                item_master = item.itemmaster
                
                if self.gst_transaction.gst_nature_type == "Specify" and self.gst_transaction.specify_type == "taxable":
                    
                    if self.gst_transaction.place_of_supply == "Intrastate":
                        
                        if (
                            self.to_decimal(item.sgst) != self.to_decimal(self.gst_transaction.sgst_rate) or
                            self.to_decimal(item.cgst) != self.to_decimal(self.gst_transaction.cgst_rate) or
                            self.to_decimal(item.cess) != self.to_decimal(self.gst_transaction.cess_rate)
                        ):
                            return False
                        
                    elif self.gst_transaction.place_of_supply == "Interstate":
                        if (
                            self.to_decimal(item.igst) != self.to_decimal(self.gst_transaction.igst_rate) or
                            self.to_decimal(item.cess) != self.to_decimal(self.gst_transaction.cess_rate)
                        ):
                            return False

                elif  self.gst_transaction.gst_nature_type == "As per HSN":
                    hsn = item.hsn
                    if ((self.to_decimal(item.sgst))  + self.to_decimal(item.cgst) + self.to_decimal(item.igst) ) != self.to_decimal(hsn.gst_rates.rate) or self.to_decimal(item.cess)  != self.to_decimal(hsn.cess_rate):
                        return False

                else:
                    # Fallback check — if all 4 rates are present, reject
                    if (self.to_decimal(item.sgst)) or self.to_decimal(item.cgst) or self.to_decimal(item.igst) or self.to_decimal(item.cess):
                        return False
                
                # TDS
                if self.tds == "P" and item_master.tds_link:
                    if item_master.tds_link.percent_individual_with_pan != item.tds_percentage:
                        
                        return False
                elif self.tds == "O" and item_master.tds_link:
                        if item_master.tds_link.percent_other_with_pan != item.tds_percentage:
                            
                            return False
                else:
                    if item.tds_percentage and  item.tds_percentage > 0:
                        
                        return False
                
                # TCS
                if self.tcs == "WP" and item_master.tcs_link:
                    
                    
                    if item_master.tcs_link.percent_individual_with_pan != item.tcs_percentage:
                        
                        return False
                    
                elif self.tcs == "WO" and item_master.tcs_link:
                    if item_master.tcs_link.percent_other_with_pan != item.tcs_percentage:
                        
                        return False
                    
                elif self.tcs == "WOO" and item_master.tcs_link:
                    if item_master.tcs_link.percent_other_without_pan != item.tcs_percentage:
                        
                        return False
                    
                else:
                    if item.tcs_percentage and item.tcs_percentage > 0:
                        
                        return False

        if self.old_account:
            for item in self.old_account:
                account_master = item.account_master
                
                if not item.hsn:
                    continue

                if self.gst_transaction.gst_nature_type == "Specify" and self.gst_transaction.specify_type == "taxable":

                    if self.gst_transaction.place_of_supply == "Intrastate":
                        if (
                            self.to_decimal(item.sgst) != self.to_decimal(self.gst_transaction.sgst_rate) or
                            self.to_decimal(item.cgst) != self.to_decimal(self.gst_transaction.cgst_rate) or
                            self.to_decimal(item.cess) != self.to_decimal(self.gst_transaction.cess_rate)
                        ):
                            return False
                    elif self.gst_transaction.place_of_supply == "Interstate":
                        if (
                            self.to_decimal(item.igst) != self.to_decimal(self.gst_transaction.igst_rate) or
                            self.to_decimal(item.cess) != self.to_decimal(self.gst_transaction.cess_rate)
                        ):
                            return False

                elif  self.gst_transaction.gst_nature_type == "As per HSN":
                    hsn = item.hsn
                    if ((item.sgst or 0) + (item.cgst or 0) + (item.igst or 0)) != hsn.gst_rates.rate or (item.cess or 0) !=(hsn.cess_rate or 0):
                        return False

                else:
                    # Fallback check — if all 4 rates are present, reject
                    if item.sgst or item.cgst or item.igst or item.cess:
                        return False
                
                # TDS
                if self.tds == "P" and account_master.tds_link: 
                    if account_master.tds_link.percent_individual_with_pan != item.tds_percentage:
                        return False
                
                elif self.tds == "O" and account_master.tds_link:
                        if account_master.tds_link.percent_other_with_pan != item.tds_percentage:
                            return False
                
                else:
                    if item.tds_percentage and  item.tds_percentage > 0:
                        return False
                
                # TCS
                if self.tcs == "WP" and account_master.tcs_link:
                    if account_master.tcs_link.percent_individual_with_pan != item.tcs_percentage:
                        return False
                    
                elif self.tcs == "WO" and account_master.tcs_link:
                    if account_master.tcs_link.percent_other_with_pan != item.tcs_percentage:
                        return False
                    
                elif self.tcs == "WOO" and account_master.tcs_link:
                    if account_master.tcs_link.percent_other_without_pan != item.tcs_percentage:
                        return False
                    
                else:
                    if item.tcs_percentage and item.tcs_percentage > 0:
                        return False
        
        return True

    def update_tax_item_details(self):
        company = company_info()

        if company is None:
            self.errors.append("Company Not Found.")
            return False
        
        item_details = self.kwargs.get('item_details', [])
        other_charge = self.kwargs.get('other_income_charge', [])
        accounts = self.kwargs.get('accounts', [])
        other_income_instance = self.old_other_income_instances
        account_instance = self.old_account
        buyer_state =  self.credit_note.buyer_state
        updated_item_details = []
        updated_accounts = []
        
        
        if item_details:
            for item, instance_item in zip(item_details, self.old_item_details_instances):
                item['sgst'] = "0"
                item['cgst'] = "0"
                item['cess'] = "0"
                item['tax']  =  "0"
                item['igst'] = "0"
                item['tds_percentage'] = "0"
                item['tds_value'] = "0"
                item['tcs_percentage'] = "0"
                item['tcs_value'] = "0"
                

                item_master = instance_item.itemmaster  
                if self.tds == "P" and item_master.tds_link:
                    item['tds_percentage'] = str(item_master.tds_link.percent_individual_with_pan)
                    item['tds_value'] = str((item.amount*item_master.tds_link.percent_individual_with_pan)/100)
                
                elif self.tds == "O" and item_master.tds_link:
                    item['tds_percentage'] = str(item_master.tds_link.percent_other_with_pan)
                    item['tds_value'] = str((item.amount*item_master.tds_link.percent_other_with_pan)/100)
                
                if self.tcs == "WP" and item_master.tcs_link:
                    item['tcs_percentage'] = str(item_master.tcs_link.percent_individual_with_pan)
                    item['tcs_value'] = str((item.amount*item_master.tcs_link.percent_individual_with_pan)/100)
                
                elif self.tcs == "WO" and item_master.tcs_link:
                    item['tcs_percentage'] = str(item_master.tcs_link.percent_other_with_pan)
                    item['tcs_value'] = str((item.amount*item_master.tcs_link.percent_other_with_pan)/100)
                
                elif self.tcs == "WOO" and item_master.tcs_link:
                    item['tcs_percentage'] = str(item_master.tcs_link.percent_other_without_pan)
                    item['tcs_value'] = str((item.amount*item_master.tcs_link.percent_other_without_pan)/100)



                if self.gst_transaction.gst_nature_type == "Specify" and self.gst_transaction.specify_type == "taxable":
                    if self.gst_transaction.place_of_supply == "Intrastate":
                        item['sgst'] = str(self.gst_transaction.sgst_rate)
                        item['cgst'] = str(self.gst_transaction.cgst_rate)
                        item['cess'] = str(self.gst_transaction.cess_rate)
                        item['tax'] = str(self.gst_transaction.sgst_rate+self.gst_transaction.cgst_rate+self.gst_transaction.cess_rate)
                    else:
                        item['igst'] = str(self.gst_transaction.igst_rate)
                        item['cess'] = str(self.gst_transaction.cess_rate)
                        item['tax'] =  str(self.gst_transaction.igst_rate+self.gst_transaction.cess_rate)
                    
                elif self.gst_transaction.gst_nature_type == "As per HSN":
                    if str(buyer_state).lower() == str(company.address.state).lower():
                        rate_half = instance_item.hsn.gst_rates.rate / 2
                        item['sgst'] =str(rate_half or 0)
                        item['cgst'] =str(rate_half or 0)
                        item['cess'] =str(instance_item.hsn.cess_rate or 0)
                        item['tax'] = str(instance_item.hsn.gst_rates.rate or 0)
                    else: 
                        item['igst'] =str(instance_item.hsn.gst_rates.rate or 0)
                        item['cess'] =str(instance_item.hsn.cess_rate or 0)
                        item['tax'] = str(instance_item.hsn.gst_rates.rate or 0)
                
                updated_item_details.append(item)
                
        
        if other_charge:
            for charge, instance_charge in zip(other_charge, other_income_instance):
                
                if self.gst_transaction.gst_nature_type == "Specify" and self.gst_transaction.specify_type == "taxable":
                    if self.gst_transaction.place_of_supply == "Intrastate":
                        charge['sgst'] = str(self.gst_transaction.sgst_rate)
                        charge['cgst'] = str(self.gst_transaction.cgst_rate)
                        charge['cess'] = str(self.gst_transaction.cess_rate)
                        charge['tax'] = str(self.gst_transaction.sgst_rate+self.gst_transaction.cgst_rate+self.gst_transaction.cess_rate)
                    else:
                        charge['igst'] = str(self.gst_transaction.igst_rate)
                        charge['cess'] = str(self.gst_transaction.cess_rate)
                        charge['tax'] =  str(self.gst_transaction.igst_rate+self.gst_transaction.cess_rate)

                elif self.gst_transaction.gst_nature_type == "As per HSN":
                    if str(buyer_state).lower() == str(company.address.state).lower():
                        hsn = instance_charge.other_income_charges.hsn
                        rate_half = hsn.gst_rates.rate / 2
                        charge['sgst'] =str(rate_half or 0)
                        charge['cgst'] =str(rate_half or 0)
                        charge['cess'] =str(hsn.gst_rates.cess_rate or 0)
                        charge['tax'] = str(hsn.gst_rates.rate or 0)
                    else: 
                        charge['igst'] =str(hsn.gst_rates.rate or 0)
                        charge['cess'] =str(hsn.gst_rates.cess_rate or 0)
                        charge['tax'] = str(hsn.gst_rates.rate or 0)
                self.updated_other_income.append(charge)
         
        if accounts:
            
            for account, instance_acount in zip(accounts, account_instance):
                account['sgst'] = "0"
                account['cgst'] = "0"
                account['cess'] = "0"
                account['tax'] = "0"
                account['igst'] = "0"
                account_master = instance_acount.account_master

                if not instance_acount.hsn:
                    continue
                
                
                # amount = account.amount 
                if  self.tds == "P" and account_master.tds_link:
                    account['tds_percentage'] = str(account_master.tds_link.percent_individual_with_pan)
                    # account['tdsValue'] = str((amount*account_master.tds_link.percent_individual_with_pan)/100)
                elif self.tds == "O" and account_master.tds_link:
                    account['tds_percentage'] = str(account_master.tds_link.percent_other_with_pan)
                    # account['tds_value'] = str((amount*account_master.tds_link.percent_other_with_pan)/100)
                
                # TCS
                if self.tcs == "WP" and account_master.tcs_link:
                    account['tcs_percentage'] = str(account_master.tcs_link.percent_individual_with_pan)
                    # account['tcsValue'] = str((amount*account_master.tcs_link.percent_individual_with_pan)/100)
                elif self.tcs == "WO" and account_master.tcs_link:
                    account['tcs_percentage'] = str(account_master.tcs_link.percent_other_with_pan)
                    # account['tcsValue'] = str((amount*account_master.tcs_link.percent_other_with_pan)/100)
                elif self.tcs == "WOO" and account_master.tcs_link:
                    account['tcs_percentage'] = str(account_master.tcs_link.percent_other_without_pan)
                    # account['tcsValue'] = str((amount*account_master.tcs_link.percent_other_without_pan)/100)

                if self.gst_transaction.gst_nature_type == "Specify" and self.gst_transaction.specify_type == "taxable":
                    if self.gst_transaction.place_of_supply == "Intrastate":
                        account['sgst'] = str(self.gst_transaction.sgst_rate)
                        account['cgst'] = str(self.gst_transaction.cgst_rate)
                        account['cess'] = str(self.gst_transaction.cess_rate)
                        account['tax'] = str(self.gst_transaction.sgst_rate+self.gst_transaction.cgst_rate+self.gst_transaction.cess_rate)
                    else:
                        account['igst'] = str(self.gst_transaction.igst_rate)
                        account['cess'] = str(self.gst_transaction.cess_rate)
                        account['tax'] =  str(self.gst_transaction.igst_rate+self.gst_transaction.cess_rate)
                
                elif self.gst_transaction.gst_nature_type == "As per HSN":
                    if str(buyer_state).lower() == str(company.address.state).lower():
                        hsn = instance_acount.hsn
                        rate_half = hsn.gst_rates.rate / 2
                        account['sgst'] =str(rate_half or 0)
                        account['cgst'] =str(rate_half or 0)
                        account['cess'] =str(hsn.gst_rates.cess_rate or 0)
                        account['tax'] = str(hsn.gst_rates.rate or 0)
                    else:
                        account['igst'] =str(hsn.gst_rates.rate or 0)
                        account['cess'] =str(hsn.gst_rates.cess_rate or 0)
                        account['tax'] = str(hsn.gst_rates.rate or 0)
                updated_accounts.append(account)
        

        combined_list = updated_item_details+updated_accounts
        item_detail_and_account_list = sorted(combined_list, key=lambda x: int(x["index"]))
        
        self.updated_item_details.extend(item_detail_and_account_list)
        
        return True

    # Main process flows
    def process(self) -> dict:
        with transaction.atomic():
            if self.status_text == "Draft":
                print("dart1")
                if not self.get_credit_note():
                    return self.response()
                print("dart2")
                if not self.validate_required_fields():
                    return self.response()
                print("dart3")
                if not self.update_status_instance():
                    return self.response()
                print("dart4")
                if not self.validate_numbering():
                    return self.response()
                print("dart5")
                if not self.validate_item_details():
                    return self.response()
                print("dart6")
                if not self.validate_other_charges():
                    return self.response()
                print("dart7")
                if not self.validate_account():
                    return self.response()
                print("dart8")
                if not self.save_item_details():
                    return self.response()
                print("dart9")
                if not self.save_other_income_charges():
                    return self.response()
                print("dart10")
                if not self.save_account():
                    return self.response()
                print("dart11")
                if not self.save_credit_note():
                    return self.response()
                
                self.success = True
            
            elif self.status_text == "Submit":
                if not self.get_credit_note():
                    return self.response()
                print("Submit 1")
                if not self.validate_required_fields():
                    return self.response()
                print("Submit 2")
                if not self.update_status_instance():
                    return self.response()
                print("Submit 3")
                if not self.validate_item_detail_on_submit():
                    return self.response()
                print("Submit 4")
                if not self.validate_tax():    
                    print("***"*3)
                    self.update_tax_item_details()
                    return self.response()
                print("Submit 5")
                self.credit_note.status = self.status
                self.credit_note.save()
                self.success = True
            
            else:
                self.errors.append(f"{self.status_text} Unexpected status.")
        return self.response()

    #  Response structure
    def response(self)-> dict:
        return {
            "credit_note_invoice": self.credit_note,
            "success": self.success,
            "errors": self.errors,
            "item_detail" :  self.updated_item_details if self.updated_item_details else None ,
            "other_income_charges" :self.updated_other_income if self.updated_other_income else None 
        }


def credit_note_genral_update(data):
    valid_serializers = []
    errors = []
    credit = data.get("credit", {})
    debits = data.get("debits", [])

    debits_amount = Decimal("0.00")
    REQUIRED_FIELDS = ["date", "voucher_type", "credit_note_voucher_no", "account", "created_by"]

    # Process debit
    for idx, debit in enumerate(debits):
        for field in REQUIRED_FIELDS + ["debit"]:
            if debit.get(field) in [None, ""]:
                errors.append(f"debit [{idx}] → '{field}' is required.")
        
        debits_amount += debit.get("debit", 0)
        serializer = AccountsGeneralLedgerSerializer(data=debit)
        if not serializer.is_valid():
            for field, error in serializer.errors.items():
                errors.append(f"credit [{idx}] → {field}: {'; '.join(map(str, error))}")
        else:
            valid_serializers.append(serializer)

    # Process credit
    for field in REQUIRED_FIELDS + ["credit"]:
        if credit.get(field) in [None, ""]:
            errors.append(f"credit → '{field}' is required.")

    serializer = AccountsGeneralLedgerSerializer(data=credit)
    if not serializer.is_valid():
        for field, error in serializer.errors.items():
            errors.append(f"credit → {field}: {'; '.join(map(str, error))}")
    else:
        valid_serializers.append(serializer)

    # Compare debit and credit amounts
    credit_amount = Decimal(str(credit.get("credit", 0)))
    if credit_amount != debits_amount:
        errors.append(f"Debit amount ({debits_amount}) and credit amount ({credit_amount}) do not match.----")

    # Return errors if any
    if errors:
        return {"success": False, "errors": errors}

    # Save all valid serializers
    for valid_serializer in valid_serializers:
        valid_serializer.save()

    return {"success": True, "errors": []}