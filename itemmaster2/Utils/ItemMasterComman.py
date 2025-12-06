from decimal import Decimal, ROUND_DOWN
from itemmaster.views import *
from itemmaster2.models import *
from itemmaster.views import *
from userManagement.models import *


def get_all_related_version(queryset, model):
    """get all version for this model"""
    
    version = set()  # Use a set to avoid duplicates
    version.add(queryset.id)

    def check_related(order):
        if order is None:
            return

        # Check for child orders
        child_orders = model.objects.filter(parent_order=order.id)
        for child in child_orders:
            if child.id not in version:
                version.add(child.id)
                check_related(child)

        # Check for parent order
        if order.parent_order and order.parent_order.id not in version:
            version.add(order.parent_order.id)
            check_related(order.parent_order)

    try:
        print("---", version)
        check_related(queryset)
    except Exception as e:
        print(f"Error accessing related orders for instance {queryset.id}: {e}")
    return sorted(version)  # Convert to list if needed


def get_department_view_hierarchical():
    from collections import defaultdict

    ceo = UserManagement.objects.filter(
        Q(role__role_name="CEO") | Q(role_2__role_name="CEO")
    ).first()

    if not ceo:
        return {"message": "No CEO found."}

    # Set to track visited (user_id, role_id) combinations
    visited_user_roles = set()

    def get_users_reporting_to(user, ):
        return UserManagement.objects.filter(
            Q(role__report_to=user.user) | Q(role_2__report_to=user.user)
        ).distinct()

    def get_user_roles(user, reporting_to, headRole=None):
        roles = []
        if user.role.role_name == "CEO":
            if user.role and user.role.report_to == reporting_to:
                roles.append(user.role)
            if user.role_2 and user.role_2.report_to == reporting_to:
                roles.append(user.role_2)
        else:
            if user.role and user.role.report_to == reporting_to and user.role.parent_role.id == headRole.id:
                roles.append(user.role)
            if user.role_2 and user.role_2.report_to == reporting_to and user.role.parent_role.id == headRole.id:
                roles.append(user.role_2)
        return roles

    def build_hierarchy(user, reporting_to=None, headRole=None):
        role_group = defaultdict(list)

        roles = get_user_roles(user, reporting_to, headRole)
        for role in roles:
            if (user.user.id, role.id) in visited_user_roles:
                continue

            visited_user_roles.add((user.user.id, role.id))
            subordinates = get_users_reporting_to(user)

            # Prepare sub_hierarchy with merged roles
            merged_sub_hierarchy = defaultdict(list)

            for subordinate in subordinates:
                sub_result = build_hierarchy(subordinate, user.user, role)
                for role_entry in sub_result:
                    role_name = role_entry["role"]
                    merged_sub_hierarchy[role_name].extend(role_entry["users"])

            # Convert merged dict to list
            grouped_sub_hierarchy = []
            for role_name, users in merged_sub_hierarchy.items():
                grouped_sub_hierarchy.append({
                    "role": role_name,
                    "users": users
                })

            # Add user with grouped subordinates
            role_group[role.role_name].append({
                "user": user.user.username,
                "subordinates": grouped_sub_hierarchy
            })

        # Final return: list of role-grouped user blocks
        hierarchy = []
        for role_name, users in role_group.items():
            hierarchy.append({
                "role": role_name,
                "users": users
            })

        return hierarchy


    # Start building the hierarchy from the CEO
    hierarchy = build_hierarchy(ceo)

    return hierarchy



def discountApplyForitemCombo(itemCombos, amount, qty):
    total_value = sum(
        Decimal(item.rate if item.rate else item.after_discount_value_for_per_item) * item.qty
        for item in itemCombos
    )

    roundedFinalTotal = amount / qty
    totalDiscountNeeded = total_value - roundedFinalTotal

    # Calculate contributions and ratios
    item_contributions = [
        Decimal(item.rate if item.rate else item.after_discount_value_for_per_item) * item.qty for item in itemCombos
    ]
    ratios = [contribution / total_value for contribution in item_contributions]

    # Calculate the discount for each item
    discounts = [totalDiscountNeeded * ratio for ratio in ratios]

    for index, itemCombo in enumerate(itemCombos):
        try:
            original_price = Decimal(
                itemCombo.rate if itemCombo.rate else itemCombo.after_discount_value_for_per_item) * itemCombo.qty
            discounted_amount = original_price - discounts[index]
            discounted_amount = max(discounted_amount, Decimal('0.00')).quantize(Decimal('0.000'), rounding=ROUND_DOWN)

            itemCombo.after_discount_value_for_per_item = (discounted_amount / itemCombo.qty).quantize(Decimal('0.000'),
                                                                                                       rounding=ROUND_DOWN)
            itemCombo.amount = discounted_amount
            itemCombo.save()
        except Exception as e:
            print(e)

    return itemCombos
