# In-memory "database" - consolidated
inventory = []  # List of dicts: {'item': str, 'quantity': int}
donations = []  # List of dicts: {'id': int, 'donor_name': str, 'item': str, 'amount': int}
requests = []   # List of dicts: {'id': int, 'school': str, 'item': str, 'quantity': int, 'status': str}
distributions = []  # List of dicts: {'id': int, 'recipient': str, 'item': str, 'quantity': int}

# ----- Inventory functions -----
def get_inventory():
    return inventory

def add_inventory(item, quantity):
    """Add or update quantity for an item in inventory."""
    for i in inventory:
        if i['item'] == item:
            i['quantity'] += quantity
            return
    inventory.append({'item': item, 'quantity': quantity})

def deduct_inventory(item, quantity):
    """Deduct quantity from an item in inventory (if sufficient)."""
    for i in inventory:
        if i['item'] == item:
            if i['quantity'] >= quantity:
                i['quantity'] -= quantity
                if i['quantity'] == 0:
                    inventory.remove(i)  # Optional: remove if zero
            break

# ----- Donations functions -----
def get_donations():
    return donations

def add_donation(donor_name, item, amount):
    new_id = len(donations) + 1
    donations.append({
        "id": new_id,
        "donor_name": donor_name,
        "item": item,
        "amount": amount
    })

# ----- Requests functions -----
def get_requests():
    return requests

def add_request(school, item, quantity):
    new_id = len(requests) + 1
    requests.append({
        "id": new_id,
        "school": school,
        "item": item,
        "quantity": quantity,
        "status": "pending"
    })

def update_request_status(request_id, status):
    for req in requests:
        if req["id"] == request_id:
            req["status"] = status
            break

# ----- Distributions functions -----
def get_distributions():
    return distributions

def add_distribution(recipient, item, quantity):
    new_id = len(distributions) + 1
    distributions.append({
        "id": new_id,
        "recipient": recipient,
        "item": item,
        "quantity": quantity
    })