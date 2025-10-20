"""
Compatibility layer for loading inbox-sentinel models
"""
import sys
import pickle
import io


class PickleCompatLoader:
    """Custom unpickler that handles missing modules"""

    class UnpicklerCompat(pickle.Unpickler):
        def find_class(self, module, name):
            # Redirect inbox_sentinel modules to local modules
            if module.startswith('inbox_sentinel'):
                if 'preprocessing' in module or name == 'EmailPreprocessor':
                    import preprocessing
                    return getattr(preprocessing, name)
            # Try normal loading
            try:
                return super().find_class(module, name)
            except (ModuleNotFoundError, AttributeError):
                # For sklearn and numpy, use normal loading
                if module.startswith('sklearn') or module.startswith('numpy'):
                    return super().find_class(module, name)
                # Create a dummy class for unknown modules
                return type(name, (), {})

    @staticmethod
    def load(file_path):
        """Load a pickle file with compatibility handling"""
        with open(file_path, 'rb') as f:
            return PickleCompatLoader.UnpicklerCompat(f).load()
