from pydantic import BaseModel
from typing import Literal
from typing import Optional


class GeneratedMessage(BaseModel):
    role: Literal["assistant"] | str
    content: Optional[str] = None
    reasoning: Optional[str] = None
    tool_calls: Optional[list["ToolCall"]] = None


class StructuredGeneratedMessage(BaseModel):
    role: Literal["assistant"] | str
    content: BaseModel


class InputMessage(BaseModel):
    role: Literal["system", "user", "developer"] | str
    content: "InputMessageContent"


class InputMessageContent(BaseModel):
    type: Literal["text", "image_url", "file"]
    file: Optional["File"] = None
    text: Optional[str] = None
    image_url: Optional["ImageURL"] = None


class File(BaseModel):
    file_data: str
    """
    The base64 encoded file data, used when passing the file to the model as a
    string.
    """

    file_id: str
    """The ID of an uploaded file to use as input."""

    filename: str
    """The name of the file, used when passing the file to the model as a string."""


class ImageURL(BaseModel):
    url: str
    """Either a URL of the image or the base64 encoded image data."""


class ToolCallContent(BaseModel):
    arguments: str
    name: str


class ToolCall(BaseModel):
    id: str
    function: ToolCallContent
    type: Literal["function"] = "function"
