from conjugate import SimpleTense, conjugate_as_regular


def test_finire_present() -> None:
    c = conjugate_as_regular("finire")
    assert c[SimpleTense.PRESENT] == [
        "finisco",
        "finisci",
        "finisce",
        "finiamo",
        "finite",
        "finiscono",
    ]


def test_condurre_present() -> None:
    c = conjugate_as_regular("condurre")
    assert c[SimpleTense.PRESENT] == [
        "conduo",
        "condui",
        "condue",
        "conduiamo",
        "conduete",
        "conduono",
    ]


def test_diversificarsi_passato_remoto() -> None:
    c = conjugate_as_regular("diversificarsi")
    assert c[SimpleTense.PASSATO_REMOTO] == [
        "mi diversificai",
        "ti diversificasti",
        "si diversificò",
        "ci diversificammo",
        "vi diversificaste",
        "si diversificarono",
    ]
