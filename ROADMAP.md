
# PharmDS Roadmap

This document outlines planned and exploratory directions for the PharmDS project.  
It is not a commitment or timeline, and priorities may change as the project evolves.

PharmDS is currently in **v0 (early development)**. Stability, APIs, and rule schemas may change.

----------
## Current State

PharmDS has a stable development baseline:
- Automated CI with linting and tests
- Reproducible local development setup
- Clear contribution and testing standards

Current work prioritizes correctness, explainability, and reduction of false positives.

### Contributor experience
- Maintain clear contribution and testing guidelines
- Expand golden and negative test scenarios
- Improve rule authoring clarity and reviewability

## Near-Term Focus (v0.x)

These items focus on improving correctness, clarity, and usability of the existing system.

-   Expand and refine PK and PD interaction rules
    
-   Improve rule combination and severity escalation logic
    
-   Strengthen rule validation and test coverage
    
-   Improve explanation quality and consistency
    
-   Add structured output formats (e.g., JSON) for downstream use
    
-   Improve CLI ergonomics and error handling
    

----------

## Mid-Term Exploration (Pre–v1.0)

These areas may be explored as the core stabilizes.

-   Optional patient-context modifiers (age, renal/hepatic function, risk factors)
    
-   Dose-aware or conditional interaction logic
    
-   Rule authoring and review tooling
    
-   Initial Web UI for interactive exploration of interactions
    
-   Improved internal data modeling and normalization
    

----------

## Longer-Term Possibilities

These items are speculative and dependent on scope, licensing, and resources.

-   Broader drug coverage and pharmacologic attributes
    
-   Integration with curated external data sources (where permitted)
    
-   Interoperability with other clinical or educational tools
    
-   Export formats suitable for teaching, research, or safety review workflows
    

----------

## Non-Goals

To keep scope clear, PharmDS explicitly does **not** aim to:

-   Replace clinical judgment or prescribing decisions
    
-   Act as a diagnostic or treatment recommendation system


----------

## Contribution Notes

PharmDS prioritizes:

-   explicit, traceable logic
    
-   explainability over prediction
    
-   conservative safety defaults
    

Contributions aligned with these principles are encouraged.
