from app.services.mapper import PayloadMapper, PayloadMappingConfig, MappingRule, MappingField
from app.schemas.payload import NormalizedPayload

def test_mapper_flat_messy_json():
    # Setup mock config
    config = PayloadMappingConfig(
        mappings=[
            MappingRule(
                source_pattern=".*",
                fields=[
                    MappingField(target="record_id", json_path="$.id"),
                    MappingField(target="source", json_path="$.system"),
                    MappingField(target="captured_at", json_path="$.timestamp"),
                    MappingField(target="financials.total_price", json_path="$.val", type_cast="float"),
                    MappingField(target="financials.margin", json_path="$.profit_pct", type_cast="float"),
                    MappingField(target="documents.so_summary_found", json_path="$.has_doc", type_cast="boolean"),
                    MappingField(target="metadata.payload_version", json_path="$.ver")
                ]
            )
        ]
    )
    
    mapper = PayloadMapper(config=config)
    
    messy_payload = {
        "id": "OPP-999",
        "system": "LegacyScraper",
        "timestamp": "2026-07-07T12:00:00Z",
        "val": "150000.50",
        "profit_pct": "0.45",
        "has_doc": "yes",
        "ver": "v2"
    }
    
    mapped = mapper.map_payload(messy_payload)
    
    # Validate it parses correctly into NormalizedPayload
    validated = NormalizedPayload(**mapped)
    
    assert validated.record_id == "OPP-999"
    assert validated.source == "legacyscraper" # it normalizes source
    assert validated.financials.total_price == 150000.50
    assert validated.financials.margin == 0.45
    assert validated.documents.so_summary_found is True
    assert validated.metadata.payload_version == "v2"
