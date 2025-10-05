def test_reexports_exist_without_import_error():
    import domain as d
    # Touch a few re-exports; this will fail only if circular imports exist.
    assert d.Match and d.Score and d.Result
