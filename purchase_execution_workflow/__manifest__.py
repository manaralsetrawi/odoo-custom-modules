{
    'name': 'Purchase Execution Workflow',
    'version': '1.0',
    'summary': 'Custom procurement flow extensions for purchase orders',
    'category': 'Purchase',
    'author': 'Manar Alsetrawi',
    'depends': ['purchase', 'stock', 'account'], #later add the custom module name for the purchase request
    'data': [
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
}