# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval

__all__ = ['ExternalReceptionLine']
__metaclass__ = PoolMeta


class ExternalReceptionLine:
    __name__ = 'stock.external.reception.line'
    lot = fields.Many2One('stock.lot', 'Lot', domain=[
            ('product', '=', Eval('product')),
            ], depends=['product'])

    @fields.depends('lot')
    def on_change_product(self):
        res = super(ExternalReceptionLine, self).on_change_product()
        if self.product and self.lot and self.lot.product == self.product:
            return res
        res['lot'] = None
        return res

    def _get_move(self):
        move = super(ExternalReceptionLine, self)._get_move()
        move.lot = self.lot
        return move
