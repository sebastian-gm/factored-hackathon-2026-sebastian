from dataclasses import replace

import pytest

from aclara.agent.selection import candidates
from aclara.bank.repository import TransactionRepository


@pytest.mark.parametrize("merchant", ["Tienda 24", "Cafe-62", "Nube 101"])
def test_merchant_numbers_do_not_become_an_amount(merchant):
    row = replace(TransactionRepository()._rows[0], merchant_name=merchant, amount=71.35)
    rows = [("target", row)]
    assert candidates(f"No hice el cargo de {merchant}", rows) == (rows, False)
    assert candidates(f"Não fiz a compra em {merchant} de 71,35 USD", rows) == (rows, False)
    assert candidates(f"No hice el cargo de {merchant} por 12 USD", rows)[0] == []
    assert candidates(f"Estado del cargo de {merchant} del 2026-06-08", rows) == (rows, False)
    # A date alone is not transaction identification.
    assert candidates("Cargo del 2026-06-08", rows)[1] is True
