# Changelog

## [0.2.0] - CLI Refactoring & Enhanced Core Features
- **CLI Refactoring**: Restructured CLI into modular package (`core.py`, `display.py`, `prompts.py`) following SOLID principles
- **Parameter Metadata**: Added `ParameterMetadata` class for rich parameter descriptions, defaults, validators, and required/optional flags
- **Context Management**: Enhanced context system with history snapshots, restore functionality, and context-aware defaults
- **Event Hooks**: Comprehensive pre/post/error hook system for function execution monitoring
- **Advanced Parameter Sources**: 
  - `ListParamSource` for collection inputs with custom separators
  - `FileParamSource` for file content as parameters
  - `ContextParamSource` for bridge context values
  - Enhanced `MenuParamSource` with Enum support
- **Multiple Output Destinations**: Support for multiple outputs per function (display, file, context)
- **Rich CLI Interface**: Enhanced CLI with parameter descriptions, validation feedback, and improved help system
- **Type Safety**: Comprehensive type annotations and Pydantic validation throughout
- **Extensible Architecture**: Improved extensibility for custom parameter sources and output destinations

## [0.1.0] - Initial Release
- Minimal, extensible core for registering and running Python functions as bridges
- Automatic parameter extraction from function signatures
- Support for custom parameter sources and output destinations
- Basic CLI interface for interactive function execution
- Example usage and tests included 