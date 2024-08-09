import unittest
from decimal import Decimal

from proteus import Model
from trytond.model.modelstorage import RequiredValidationError
from trytond.modules.company.tests.tools import create_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Install stock_external_reception_lot
        config = activate_modules('stock_external_reception_lot')

        # Create company
        _ = create_company()

        # Create stock user
        User = Model.get('res.user')
        Group = Model.get('res.group')
        stock_user = User()
        stock_user.name = 'Stock'
        stock_user.login = 'stock'
        stock_group, = Group.find([('name', '=', 'Stock')])
        stock_user.groups.append(stock_group)
        stock_user.save()

        # Create customer
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.save()

        # Create two products that require lot
        ProductUom = Model.get('product.uom')
        ProductTemplate = Model.get('product.template')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        template1 = ProductTemplate()
        template1.name = 'Product'
        template1.default_uom = unit
        template1.type = 'goods'
        template1.list_price = Decimal('20')
        template1.lot_required = ['storage']
        template1.save()
        product1, = template1.products
        template2 = ProductTemplate()
        template2.name = 'Product'
        template2.default_uom = unit
        template2.type = 'goods'
        template2.list_price = Decimal('20')
        template2.lot_required = ['storage']
        template2.save()
        product2, = template2.products

        # Get stock locations
        Location = Model.get('stock.location')
        storage_loc, = Location.find([('code', '=', 'STO')])

        # Recieve products from customer
        config.user = stock_user.id
        Reception = Model.get('stock.external.reception')
        reception = Reception()
        reception.reference = '1234'
        reception.party = customer
        line = reception.lines.new()
        line.description = 'Test product'
        line.quantity = 1
        reception.click('receive')

        # Set product and lot to reception line and check lot is empty when change
        # product
        Lot = Model.get('stock.lot')
        Reception = Model.get('stock.external.reception')
        lot1 = Lot()
        lot1.number = '1'
        lot1.product = product1
        lot1.save()
        lot2 = Lot()
        lot2.number = '2'
        lot2.product = product2
        lot2.save()
        reception = Reception(reception.id)
        line, = reception.lines
        line.product = product1
        line.lot = lot1
        self.assertEqual(line.lot.number, '1')
        line.product = product2
        self.assertEqual(line.lot, None)

        # Required lot error is raised if lot is not supplied in reception line for a
        # product that requires lot
        with self.assertRaises(RequiredValidationError):
            reception.click('done')
        line, = reception.lines
        line.lot = lot2
        reception.click('done')
        shipment, = reception.shipments
        self.assertEqual(shipment.party, reception.party)
        self.assertEqual(shipment.state, 'done')
        self.assertEqual(shipment.effective_date, reception.effective_date)
        move, = shipment.moves
        self.assertEqual(move.state, 'done')
        self.assertEqual(move.product, product2)
        self.assertEqual(move.lot, lot2)
        self.assertEqual(move.quantity, 1.0)
        self.assertEqual(move.uom, unit)
        self.assertEqual(move.from_location, customer.customer_location)
        self.assertEqual(move.to_location, storage_loc)
