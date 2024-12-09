from pydantic import BaseModel
from typing import Optional


class nugget_model(BaseModel):
    frontend_id: str
    collection: str
    card_title: str
    knowledge_source: str
    technology: list
    development_scope: str
    context_background: str
    lob: list
    functionality_in_scope: str
    functionality_out_of_scope: Optional[str]
    artifact_tag: list
    system_demo: Optional[str]
    system_demo_document_number: Optional[str]
    demo_presentation_link: Optional[str]
    features_enabled: Optional[list]
    functional_specification_document_link: str
    requirement_document_link: Optional[str]
    technical_specification_document_link: Optional[str]
    requested_by: str
    requested_on: str
    status: str
    approver: str
    approver_remark: str
    approved_or_rejected_on: str
    parent_nugget: Optional[str]
    is_restricted_nugget: str
    nugget_access_to: Optional[list]
    version: str

class duplicate_nugget_model(BaseModel):
    collection: str
    card_title: str
    knowledge_source: str
    technology: list
    development_scope: str
    context_background: str
    lob: list
    functionality_in_scope: str
    functionality_out_of_scope: Optional[str]
    artifact_tag: list
    system_demo: Optional[str]
    features_enabled: Optional[list]


# class create_token(BaseModel):
#     # client_id:str = Header(..., description=user name for validation)
#     # client_secret:str = Header(..., description=user password for validation)
#     client_id:Annotated[str, Header()] = None
#     client_secret:Annotated[str, Header()] = None

class Token(BaseModel):
    status: str
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    disabled: bool = None


class search_data(BaseModel):
    query: str
    artifact_tag: list = None
    # dynamic_tag:list = None
    collection: Optional[list] = None
    document_from:str
    development_scope:Optional[str]
    system_demo:Optional[str]
    features_enabled:Optional[list]


class UserInDB(User):
    hashed_password: str


class TokenData(BaseModel):
    username: str = None


class comment_model(BaseModel):
    comment: str
    user_name: str
    commented_on: str


class document_model(BaseModel):
    demo_presentation_document_link: Optional[str] = None
    functional_specification_document_link: Optional[str] = None
    requirement_document_link: Optional[str] = None
    technical_specification_document_link: Optional[str] = None

class sharepoint_search_model(BaseModel):
    query:str