from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import BooleanProperty
from kivy.uix.widget import Widget
import kivy.utils  # Just in case we need color utils later
from backend import *

# Quick setup for window size - makes it look like mobile on desktop
Window.size = (400, 600)

# Some KV rules to standardize buttons and labels - keeps things consistent
Builder.load_string('''
<CustomButton@Button>:
    size_hint_y: None
    height: '40dp'
    font_size: '14sp'
<CustomLabel@Label>:
    size_hint_y: None
    height: '30dp'
    font_size: '12sp'
''')

# Themes defined as dicts - easy to switch between light/dark
LIGHT_THEME = {
    'bg_color': (1, 1, 1, 1),  # White bg
    'text_color': (0, 0, 0, 1),  # Black text
    'btn_bg': (0.9, 0.9, 0.9, 1),  # Light gray for buttons
    'input_bg': (1, 1, 1, 1),  # White for inputs
    'error_color': (1, 0, 0, 1),  # Red errors
}

DARK_THEME = {
    'bg_color': (0.2, 0.2, 0.2, 1),  # Dark bg
    'text_color': (1, 1, 1, 1),  # White text
    'btn_bg': (0.9, 0.9, 0.9, 1),  # Same button bg for now
    'input_bg': (0.25, 0.25, 0.25, 1),  # Dark input
    'error_color': (1, 0.5, 0.5, 1),  # Lighter red for dark mode
}

# Function to apply theme everywhere - recursive so it hits all kids
def apply_theme_recursively(widget, theme):
    """Goes through widget tree and sets colors based on theme."""
    # Handle labels
    if isinstance(widget, Label):
        widget.color = theme['text_color']
    # Buttons and toggles
    if isinstance(widget, (Button, ToggleButton)):
        widget.color = theme['text_color']
        widget.background_color = theme['btn_bg']  # Force bg color
    # Text inputs
    if isinstance(widget, TextInput):
        widget.foreground_color = theme['text_color']
        widget.background_color = theme['input_bg']
    
    # Keep going down the tree
    for child in widget.children:
        apply_theme_recursively(child, theme)

# Base class for themed screens - handles dark mode prop
class ThemedWidget(Widget):
    dark_mode = BooleanProperty(True)  # Starts dark, like the wireframes suggest
    
    def __init__(self, **kwargs):
        super(ThemedWidget, self).__init__(**kwargs)
        self.apply_theme(True)  # Init with dark
    
    def on_dark_mode(self, instance, value):
        # Pick theme and apply
        theme = DARK_THEME if value else LIGHT_THEME
        apply_theme_recursively(self, theme)
        Window.clearcolor = theme['bg_color']
    
    def apply_theme(self, is_dark):
        self.dark_mode = is_dark  # This triggers the property change

# Dashboard - sidebar nav, with dynamic content for totals, low stock, recent requests
class DashboardScreen(ThemedWidget, Screen):
    def __init__(self, **kwargs):
        super(DashboardScreen, self).__init__(**kwargs)
        main_layout = BoxLayout(orientation='horizontal')
        
        # Sidebar - vertical buttons for nav
        sidebar = BoxLayout(orientation='vertical', size_hint_x=0.25, spacing=5, padding=5)
        sidebar.add_widget(Label(text='SupplyBridge', size_hint_y=None, height='40dp', font_size='16sp'))
        
        # Nav buttons
        alerts_btn = Button(text='Critical Alerts')
        alerts_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'alerts'))
        sidebar.add_widget(alerts_btn)
        
        donations_btn = Button(text='Donations')
        donations_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'donations'))
        sidebar.add_widget(donations_btn)
        
        inventory_btn = Button(text='Inventory')
        inventory_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'inventory'))
        sidebar.add_widget(inventory_btn)
        
        requests_btn = Button(text='Request')
        requests_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'requests'))
        sidebar.add_widget(requests_btn)
        
        distribution_btn = Button(text='Distribution')
        distribution_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'distribution'))
        sidebar.add_widget(distribution_btn)
        
        settings_btn = Button(text='Settings')
        settings_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        sidebar.add_widget(settings_btn)
        
        # Exit X button at bottom
        exit_btn = Button(text='X', size_hint_y=None, height='30dp')
        exit_btn.bind(on_press=self.go_to_exit)
        sidebar.add_widget(exit_btn)
        
        main_layout.add_widget(sidebar)
        
        # Dynamic content layout
        self.content_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.total_label = Label(text='Total Items: 0', size_hint_y=None, height='30dp')
        self.low_label = Label(text='Low Stock: 0', size_hint_y=None, height='30dp')
        recent_scroll = ScrollView(size_hint_y=None, height='150dp')
        self.recent_label = Label(text='Recent Requests:\nNone', halign='left', valign='top', text_size=(None, None), size_hint_y=None, height='150dp')
        recent_scroll.add_widget(self.recent_label)
        self.content_layout.add_widget(self.total_label)
        self.content_layout.add_widget(self.low_label)
        self.content_layout.add_widget(recent_scroll)
        
        main_layout.add_widget(self.content_layout)
        
        self.add_widget(main_layout)
    
    def on_pre_enter(self, *args):
        self.refresh_content()
    
    def refresh_content(self):
        inv = get_inventory()
        total = sum(i['quantity'] for i in inv)
        self.total_label.text = f'Total Items: {total}'
        
        low_count = len([i for i in inv if i['quantity'] < 3])
        self.low_label.text = f'Low Stock: {low_count}'
        
        reqs = get_requests()[-3:]
        if reqs:
            text = 'Recent Requests:\n' + '\n'.join([f"- {r['school']}: {r['item']} x{r['quantity']} ({r['status']})" for r in reqs])
        else:
            text = 'Recent Requests:\nNone'
        self.recent_label.text = text
    
    def go_to_exit(self, instance):
        self.manager.current = 'exit_confirm'

# Critical alerts - shows low stock details dynamically
class CriticalAlertsScreen(ThemedWidget, Screen):
    def __init__(self, **kwargs):
        super(CriticalAlertsScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(text='Critical Alerts', font_size='18sp', size_hint_y=None, height='50dp')
        layout.add_widget(title)
        
        # Dynamic alerts
        self.alerts_placeholder = Label(text='No alerts at this time.', halign='center', valign='middle', text_size=(None, None))
        layout.add_widget(self.alerts_placeholder)
        
        back_btn = Button(text='Back to Dashboard', size_hint_y=None, height='40dp')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def on_pre_enter(self, *args):
        low_items = [f"- {i['item']}: {i['quantity']}" for i in get_inventory() if i['quantity'] < 3]
        if low_items:
            text = 'Low Stock Alerts:\n' + '\n'.join(low_items)
        else:
            text = 'No alerts at this time.'
        self.alerts_placeholder.text = text

# Donations list - with add button
class DonationsScreen(ThemedWidget, Screen):
    def __init__(self, **kwargs):
        super(DonationsScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(text='Donations', font_size='18sp', size_hint_y=None, height='50dp')
        layout.add_widget(title)
        
        # Scrollable area for donations
        self.donations_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.donations_layout.bind(minimum_height=self.donations_layout.setter('height'))
        
        scroll = ScrollView()
        scroll.add_widget(self.donations_layout)
        layout.add_widget(scroll)
        
        add_btn = Button(text='Add Donation', size_hint_y=None, height='50dp')
        add_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'add_donation'))
        layout.add_widget(add_btn)
        
        back_btn = Button(text='Back to Dashboard', size_hint_y=None, height='40dp')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
        
    def on_pre_enter(self, *args):
        self.refresh_list()
        
    def refresh_list(self):
        self.donations_layout.clear_widgets()
        for d in get_donations():
            self.donations_layout.add_widget(Label(
                text=f"{d['donor_name']} - {d['item']} ({d['amount']})",
                size_hint_y=None,
                height='30dp'
            ))

# Form to add a donation
class AddDonationScreen(ThemedWidget, Screen):
    def __init__(self, **kwargs):
        super(AddDonationScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(text='Add Donation', font_size='18sp', size_hint_y=None, height='50dp')
        layout.add_widget(title)
        
        self.name_input = TextInput(hint_text='Donor Name', multiline=False)
        layout.add_widget(self.name_input)
        
        self.item_input = TextInput(hint_text='Item', multiline=False)
        layout.add_widget(self.item_input)
        
        self.amount_input = TextInput(hint_text='Amount', multiline=False, input_filter='int')
        layout.add_widget(self.amount_input)
        
        submit_btn = Button(text='Submit', size_hint_y=None, height='50dp')
        submit_btn.bind(on_press=self.submit_donation)
        layout.add_widget(submit_btn)
        
        cancel_btn = Button(text='Cancel', size_hint_y=None, height='50dp')
        cancel_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'donations'))
        layout.add_widget(cancel_btn)
        
        self.add_widget(layout)
    
    def submit_donation(self, instance):
        name = self.name_input.text
        item = self.item_input.text
        amount = int(self.amount_input.text) if self.amount_input.text.isdigit() else 0

        # Call the backend function
        add_donation(name, item, amount)
        
        # Add to inventory
        add_inventory(item, amount)

        # Clear input fields so user can add another donation
        self.name_input.text = ''
        self.item_input.text = ''
        self.amount_input.text = ''
        
        self.manager.current = 'donations'

# Inventory - list with add/reduce
class InventoryScreen(ThemedWidget, Screen):
    def __init__(self, **kwargs):
        super(InventoryScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(text='Inventory', font_size='18sp', size_hint_y=None, height='50dp')
        layout.add_widget(title)
        
        # Scrollable inventory list
        self.inventory_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.inventory_layout.bind(minimum_height=self.inventory_layout.setter('height'))
        
        scroll = ScrollView()
        scroll.add_widget(self.inventory_layout)
        layout.add_widget(scroll)
        
        # Buttons for stock changes
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', spacing=10)
        add_btn = Button(text='Add Stock')
        add_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'add_stock'))
        reduce_btn = Button(text='Reduce Stock')
        reduce_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'reduce_stock'))
        btn_layout.add_widget(add_btn)
        btn_layout.add_widget(reduce_btn)
        layout.add_widget(btn_layout)
        
        back_btn = Button(text='Back to Dashboard', size_hint_y=None, height='40dp')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def on_pre_enter(self, *args):
        self.refresh_inventory()
    
    def refresh_inventory(self):
        self.inventory_layout.clear_widgets()
        for i in get_inventory():
            self.inventory_layout.add_widget(Label(
                text=f"{i['item']}: {i['quantity']}",
                size_hint_y=None,
                height='30dp'
            ))

# Add stock form
class AddStockScreen(ThemedWidget, Screen):
    def __init__(self, **kwargs):
        super(AddStockScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(text='Add Stock', font_size='18sp', size_hint_y=None, height='50dp')
        layout.add_widget(title)
        
        self.item_input = TextInput(hint_text='Item', multiline=False)
        layout.add_widget(self.item_input)
        
        self.quantity_input = TextInput(hint_text='Quantity', multiline=False, input_filter='int')
        layout.add_widget(self.quantity_input)
        
        submit_btn = Button(text='Submit', size_hint_y=None, height='50dp')
        submit_btn.bind(on_press=self.submit_add)
        layout.add_widget(submit_btn)
        
        cancel_btn = Button(text='Cancel', size_hint_y=None, height='50dp')
        cancel_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'inventory'))
        layout.add_widget(cancel_btn)
        
        self.add_widget(layout)
    
    def submit_add(self, instance):
        item = self.item_input.text
        quantity = int(self.quantity_input.text) if self.quantity_input.text.isdigit() else 0
        add_inventory(item, quantity)
        self.item_input.text = ''
        self.quantity_input.text = ''
        self.manager.current = 'inventory'

# Reduce stock form
class ReduceStockScreen(ThemedWidget, Screen):
    def __init__(self, **kwargs):
        super(ReduceStockScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(text='Reduce Stock', font_size='18sp', size_hint_y=None, height='50dp')
        layout.add_widget(title)
        
        self.item_input = TextInput(hint_text='Item', multiline=False)
        layout.add_widget(self.item_input)
        
        self.quantity_input = TextInput(hint_text='Quantity', multiline=False, input_filter='int')
        layout.add_widget(self.quantity_input)
        
        submit_btn = Button(text='Submit', size_hint_y=None, height='50dp')
        submit_btn.bind(on_press=self.submit_reduce)
        layout.add_widget(submit_btn)
        
        cancel_btn = Button(text='Cancel', size_hint_y=None, height='50dp')
        cancel_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'inventory'))
        layout.add_widget(cancel_btn)
        
        self.add_widget(layout)
    
    def submit_reduce(self, instance):
        item = self.item_input.text
        quantity = int(self.quantity_input.text) if self.quantity_input.text.isdigit() else 0
        deduct_inventory(item, quantity)
        self.item_input.text = ''
        self.quantity_input.text = ''
        self.manager.current = 'inventory'

# Requests screen - enhanced with status display and conditional buttons
class RequestsScreen(ThemedWidget, Screen):
    def __init__(self, **kwargs):
        super(RequestsScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(text='Requests', font_size='18sp', size_hint_y=None, height='50dp')
        layout.add_widget(title)
        
        # Scrollable requests
        self.requests_scroll = ScrollView()
        self.requests_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.requests_layout.bind(minimum_height=self.requests_layout.setter('height'))
        self.requests_scroll.add_widget(self.requests_layout)
        layout.add_widget(self.requests_scroll)
        
        # Add Request button
        add_request_btn = Button(text='Add Request', size_hint_y=None, height='50dp')
        add_request_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'add_request'))
        layout.add_widget(add_request_btn)
        
        back_btn = Button(text='Back to Dashboard', size_hint_y=None, height='40dp')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
        
    def on_pre_enter(self, *args):
        self.refresh_requests()
        
    def refresh_requests(self):
        self.requests_layout.clear_widgets()
        for req in get_requests():
            req_box = BoxLayout(orientation='vertical', size_hint_y=None, height='80dp' if req['status'] == 'pending' else '40dp')
            req_label = Label(
                text=f"{req['school']}: {req['item']} ({req['quantity']}) - Status: {req['status']}", 
                size_hint_y=0.6
            )
            req_box.add_widget(req_label)
            
            if req['status'] == 'pending':
                btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.4)
                accept_btn = Button(text='Accept', background_color=(0,1,0,1))  # Green
                accept_btn.bind(on_press=lambda x, r=req: self.accept_request(r))
                decline_btn = Button(text='Decline', background_color=(1,0,0,1))  # Red
                decline_btn.bind(on_press=lambda x, r=req: self.decline_request(r))
                btn_layout.add_widget(accept_btn)
                btn_layout.add_widget(decline_btn)
                req_box.add_widget(btn_layout)
                req_box.height = '80dp'
            
            self.requests_layout.add_widget(req_box)
    
    def accept_request(self, request):
        # Check if sufficient inventory
        inv = get_inventory()
        sufficient = False
        for i in inv:
            if i['item'] == request['item'] and i['quantity'] >= request['quantity']:
                sufficient = True
                break
        
        if sufficient:
            update_request_status(request['id'], 'accepted')
            add_distribution(request['school'], request['item'], request['quantity'])
            deduct_inventory(request['item'], request['quantity'])
            self.show_popup('Request accepted and distributed successfully!')
        else:
            self.show_popup('Insufficient inventory to fulfill this request.')
        
        self.refresh_requests()
    
    def decline_request(self, request):
        update_request_status(request['id'], 'declined')
        self.show_popup('Request declined.')
        self.refresh_requests()
    
    def show_popup(self, message):
        popup = Popup(title='Request Update', content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()
        # Auto-dismiss after 3 seconds
        Clock.schedule_once(lambda dt: popup.dismiss(), 3)

# Form to add a request
class AddRequestScreen(ThemedWidget, Screen):
    def __init__(self, **kwargs):
        super(AddRequestScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(text='Add Request', font_size='18sp', size_hint_y=None, height='50dp')
        layout.add_widget(title)
        
        self.school_input = TextInput(hint_text='School/Program', multiline=False)
        layout.add_widget(self.school_input)
        
        self.item_input = TextInput(hint_text='Item', multiline=False)
        layout.add_widget(self.item_input)
        
        self.quantity_input = TextInput(hint_text='Quantity', multiline=False, input_filter='int')
        layout.add_widget(self.quantity_input)
        
        submit_btn = Button(text='Submit', size_hint_y=None, height='50dp')
        submit_btn.bind(on_press=self.submit_request)
        layout.add_widget(submit_btn)
        
        cancel_btn = Button(text='Cancel', size_hint_y=None, height='50dp')
        cancel_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'requests'))
        layout.add_widget(cancel_btn)
        
        self.add_widget(layout)
    
    def submit_request(self, instance):
        school = self.school_input.text
        item = self.item_input.text
        quantity = int(self.quantity_input.text) if self.quantity_input.text.isdigit() else 0
        
        # Call backend
        add_request(school, item, quantity)
        
        # Clear fields
        self.school_input.text = ''
        self.item_input.text = ''
        self.quantity_input.text = ''
        
        self.manager.current = 'requests'

# Distribution - list with Distribute button
class DistributionScreen(ThemedWidget, Screen):
    def __init__(self, **kwargs):
        super(DistributionScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(text='Distribution', font_size='18sp', size_hint_y=None, height='50dp')
        layout.add_widget(title)
        
        # Scrollable distributions list
        self.distributions_scroll = ScrollView()
        self.distributions_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.distributions_layout.bind(minimum_height=self.distributions_layout.setter('height'))
        self.distributions_scroll.add_widget(self.distributions_layout)
        layout.add_widget(self.distributions_scroll)
        
        # Distribute button
        distribute_btn = Button(text='Distribute', size_hint_y=None, height='50dp')
        distribute_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'add_distribution'))
        layout.add_widget(distribute_btn)
        
        back_btn = Button(text='Back to Dashboard', size_hint_y=None, height='40dp')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
        
    def on_pre_enter(self, *args):
        self.refresh_distributions()
        
    def refresh_distributions(self):
        self.distributions_layout.clear_widgets()
        for dist in get_distributions():
            self.distributions_layout.add_widget(Label(
                text=f"{dist['recipient']}: {dist['item']} ({dist['quantity']})",
                size_hint_y=None,
                height='30dp'
            ))

# Form to add a distribution (deducts from inventory)
class AddDistributionScreen(ThemedWidget, Screen):
    def __init__(self, **kwargs):
        super(AddDistributionScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(text='Distribute Supplies', font_size='18sp', size_hint_y=None, height='50dp')
        layout.add_widget(title)
        
        self.recipient_input = TextInput(hint_text='School/Foundation/Program', multiline=False)
        layout.add_widget(self.recipient_input)
        
        self.item_input = TextInput(hint_text='Item', multiline=False)
        layout.add_widget(self.item_input)
        
        self.quantity_input = TextInput(hint_text='Quantity', multiline=False, input_filter='int')
        layout.add_widget(self.quantity_input)
        
        submit_btn = Button(text='Distribute', size_hint_y=None, height='50dp')
        submit_btn.bind(on_press=self.submit_distribution)
        layout.add_widget(submit_btn)
        
        cancel_btn = Button(text='Cancel', size_hint_y=None, height='50dp')
        cancel_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'distribution'))
        layout.add_widget(cancel_btn)
        
        self.add_widget(layout)
    
    def submit_distribution(self, instance):
        recipient = self.recipient_input.text
        item = self.item_input.text
        quantity = int(self.quantity_input.text) if self.quantity_input.text.isdigit() else 0
        
        # Call backend to record distribution
        add_distribution(recipient, item, quantity)
        
        # Deduct from inventory
        deduct_inventory(item, quantity)
        
        # Clear fields
        self.recipient_input.text = ''
        self.item_input.text = ''
        self.quantity_input.text = ''
        
        self.manager.current = 'distribution'

# Settings - toggles for features (no password toggle)
class SettingsScreen(ThemedWidget, Screen):
    def __init__(self, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(text='Settings', font_size='18sp', size_hint_y=None, height='50dp')
        layout.add_widget(title)
        
        # Notification toggle
        self.notif_toggle = ToggleButton(text='Notifications: On/Off', size_hint_y=None, height='50dp')
        layout.add_widget(self.notif_toggle)
        
        # Dark mode toggle - starts down (dark)
        self.dark_toggle = ToggleButton(text='Dark Mode: Active/Inactive', size_hint_y=None, height='50dp', state='down')
        self.dark_toggle.bind(on_press=self.toggle_dark_mode)
        layout.add_widget(self.dark_toggle)
        
        clear_btn = Button(text='Clear Data', size_hint_y=None, height='50dp')
        clear_btn.bind(on_press=self.clear_all_data)
        layout.add_widget(clear_btn)
        
        back_btn = Button(text='Back to Dashboard', size_hint_y=None, height='40dp')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def toggle_dark_mode(self, instance):
        # Flip dark mode for all screens
        is_dark = instance.state == 'down'
        for screen in self.manager.screens:
            screen.apply_theme(is_dark)
    
    def clear_all_data(self, instance):
        global inventory, donations, requests, distributions
        inventory.clear()
        donations.clear()
        requests.clear()
        distributions.clear()

# Confirm exit
class ExitConfirmScreen(ThemedWidget, Screen):
    def __init__(self, **kwargs):
        super(ExitConfirmScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(text='Would you like to close this application?', font_size='16sp', size_hint_y=None, height='60dp')
        layout.add_widget(title)
        
        # Yes/No buttons
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', spacing=20)
        yes_btn = Button(text='Yes', size_hint_x=0.5)
        yes_btn.bind(on_press=self.exit_app)
        no_btn = Button(text='No', size_hint_x=0.5)
        no_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def exit_app(self, instance):
        App.get_running_app().stop()

# Main app class
class SupplyBridgeApp(App):
    def build(self):
        sm = ScreenManager()
        
        # Add screens (no login-related ones)
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(CriticalAlertsScreen(name='alerts'))
        sm.add_widget(DonationsScreen(name='donations'))
        sm.add_widget(AddDonationScreen(name='add_donation'))
        sm.add_widget(InventoryScreen(name='inventory'))
        sm.add_widget(AddStockScreen(name='add_stock'))
        sm.add_widget(ReduceStockScreen(name='reduce_stock'))
        sm.add_widget(RequestsScreen(name='requests'))
        sm.add_widget(AddRequestScreen(name='add_request'))
        sm.add_widget(DistributionScreen(name='distribution'))
        sm.add_widget(AddDistributionScreen(name='add_distribution'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(ExitConfirmScreen(name='exit_confirm'))
        
        # Set dark theme on all
        for screen in sm.screens:
            screen.apply_theme(True)
        
        # Dark bg
        Window.clearcolor = DARK_THEME['bg_color']
        
        # Always start on dashboard
        sm.current = 'dashboard'
        
        return sm

# Run the app
SupplyBridgeApp().run()