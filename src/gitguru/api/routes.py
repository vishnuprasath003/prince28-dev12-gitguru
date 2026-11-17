import json

from fastapi import APIRouter, HTTPException

from gitguru.api.settings import get_settings

router = APIRouter()


def load_documents():
    settings = get_settings()

    with open(settings.data_file, "r", encoding="utf-8") as file:
        return json.load(file)


@router.get("/documents")
def get_documents():
    documents = load_documents()
    return documents


@router.get("/documents/{document_id}")
def get_document(document_id: int):
    documents = load_documents()

    for document in documents:
        if document["id"] == document_id:
            return document

    raise HTTPException(status_code=404, detail="Document not found")
