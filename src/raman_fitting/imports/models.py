from pydantic import BaseModel, FilePath, ConfigDict, computed_field

from .samples.sample_id_helpers import extract_sample_metadata_from_filepath

from .files.metadata import FileMetaData, get_file_metadata
from .files.index_helpers import get_filename_id_from_path
from .samples.models import SampleMetaData


class RamanFileInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file: FilePath

    @computed_field
    @property
    def filename_id(self) -> str:
        return get_filename_id_from_path(self.file)

    @computed_field
    @property
    def sample(self) -> SampleMetaData:
        return extract_sample_metadata_from_filepath(self.file)

    @computed_field
    @property
    def file_metadata(self) -> FileMetaData:
        return FileMetaData(**get_file_metadata(self.file))
