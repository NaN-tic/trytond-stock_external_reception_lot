# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import stock

def register():
    Pool.register(
        stock.ExternalReceptionLine,
        module='stock_external_reception_lot', type_='model')
