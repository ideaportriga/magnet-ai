from attr import dataclass


@dataclass
class IncrementalUpdateData:
    source_record_ids_to_add: list[str]
    document_ids_to_delete: list[str]
