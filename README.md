# Copernicus Land Documentation

Technical documentation for the products of the [Copernicus Global Land Service](https://land.copernicus.eu/en/products).

## Repository structure

```
docs/
├── _ancillary/          # Ancillary datasets (lake masks, river metadata, etc.)
├── _cross-cutting/      # Cross-cutting documentation (atmospheric correction, cloud masking, BRDF, QA)
├── <product>/           # One folder per product, named as <variable>_<coverage>_<resolution>_<frequency>_<version>
│   ├── *_ATBD_*.pdf     # Algorithm Theoretical Basis Document
│   ├── *_PUM_*.pdf      # Product User Manual
│   ├── *_QAR_*.pdf      # Quality Assessment Report
│   └── *_PMM_*.pdf      # Product Management Manual
```

## Product categories

Categories follow the [CLMS product catalogue](https://land.copernicus.eu/en/products).

| Category | Variables |
|---|---|
| Vegetation | NDVI, LAI, FAPAR, fCover, DMP, GDMP, GPP, NPP, BA, LSP |
| Temperature and Reflectance | LST, LST daily cycle, LST TCI, TOC |
| Water Bodies | WB, LWQ, LSWT, WL, LIE |
| Snow | SCE, SWE |
| Soil Moisture | SSM, SWI |
| Evapotranspiration | ETA, HF |
| Land Cover | LC, LCM, TCD, LCFM |
