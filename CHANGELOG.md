# Changelog

## [0.2.0] - CLI Refactoring & Enhanced Core Features
- Rich parameter metadata and validation
- Improved context management with history
- Pre/post/error event hooks
- New and enhanced parameter sources (List, File, Context, Enum)
- Multiple output destinations per function
- Expanded type safety and extensibility
- Modular CLI refactor for maintainability

## [0.1.0] - Initial Release
- Minimal, extensible core for registering and running Python functions as bridges
- Automatic parameter extraction from function signatures
- Support for custom parameter sources and output destinations
- Basic CLI interface for interactive function execution
- Example usage and tests included 

## [0.3.0] - 2024-07-01
### Added
- Multi-bridge CLI: run and switch between multiple bridges in one interface (`switch <bridge>`, `bridges` command).
- Per-bridge context and function isolation.
- Object handling: support for multiple named instances per class, with CLI and test coverage.
- CLI improvements: case-insensitive commands, built-in commands for listing instances and bridges, improved help screen.
- Refactored CLI code for clarity and maintainability.

### Fixed
- Robust parameter type handling for object/class registration.
- Pydantic validation for class constructors and methods. 