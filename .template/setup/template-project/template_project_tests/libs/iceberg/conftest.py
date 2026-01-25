import sys
from unittest.mock import Mock

# Inyectar módulo logging falso para romper import circular
mock_logging = Mock()
mock_logging.get_logger = Mock(return_value=Mock())
mock_logging.Logger = Mock()
sys.modules["template_project.libs.logging"] = mock_logging
sys.modules["template_project.libs.logging.logger"] = mock_logging
