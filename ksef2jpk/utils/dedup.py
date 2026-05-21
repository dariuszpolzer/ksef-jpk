def get_document_dedup_key(faktura):
    return faktura.nr_ksef or faktura.meta.get("nr_ksef") or faktura.meta.get("numer")
