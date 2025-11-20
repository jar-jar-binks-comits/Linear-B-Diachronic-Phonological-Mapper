"""
Tablet corpus integration
Search actual Linear B tablets
"""

import requests

class TabletCorpus:
    DAMOS_API = "http://damos.chs.harvard.edu/api"
    
    def search_word(self, transliteration):
        """Find tablets containing this word"""
        # Query DĀMOS for attestations
        pass
    
    def get_context(self, tablet_id):
        """Get full tablet text with context"""
        pass