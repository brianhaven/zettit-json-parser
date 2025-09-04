// MongoDB Script for Geographic Pattern Alias Curation
// Generated: 2025-08-26 14:04:55 PDT
// Execute in MongoDB shell or Compass

// DEPRECATE 4 business term aliases
// Move aliases to deprecated_aliases field and remove from active aliases

// Deprecate 'LI' from Liechtenstein
db.pattern_libraries.updateOne(
  { "type": "geographic_entity", "term": "Liechtenstein" },
  {
    $addToSet: { "deprecated_aliases": "LI" },
    $pull: { "aliases": "LI" }
  }
);

// Deprecate 'AC' from Acre
db.pattern_libraries.updateOne(
  { "type": "geographic_entity", "term": "Acre" },
  {
    $addToSet: { "deprecated_aliases": "AC" },
    $pull: { "aliases": "AC" }
  }
);

// Deprecate 'BI' from Burundi
db.pattern_libraries.updateOne(
  { "type": "geographic_entity", "term": "Burundi" },
  {
    $addToSet: { "deprecated_aliases": "BI" },
    $pull: { "aliases": "BI" }
  }
);

// Deprecate 'DC' from Washington DC
db.pattern_libraries.updateOne(
  { "type": "geographic_entity", "term": "Washington DC" },
  {
    $addToSet: { "deprecated_aliases": "DC" },
    $pull: { "aliases": "DC" }
  }
);

