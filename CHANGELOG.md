# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2026-05-18]

### Changed

- Migrado el sistema de gestión de dependencias de Poetry a uv
- Versión mínima de Python elevada de 3.11 a 3.13
- Cambiado build backend de `poetry-core` a `hatchling`
- Eliminado `poetry.lock`, generado `uv.lock`

## [0.1.0] - 2024-03-21

### Added

- Initial release
- Basic plugin system
- OpenAPI importer plugin
- JWT tester plugin
- HTML reporter plugin
- Configuration system
- Progress tracking
- Storage backend system
