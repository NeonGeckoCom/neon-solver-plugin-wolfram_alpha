# # NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# # All trademark and other rights reserved by their respective owners
# # Copyright 2008-2021 Neongecko.com Inc.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from datetime import timedelta
import tempfile
from os.path import join, isfile
from requests_cache import CachedSession

from neon_solvers import AbstractSolver


class WolframAlphaSolver(AbstractSolver):
    def __init__(self, config=None):
        super(WolframAlphaSolver, self).__init__(name="WolframAlpha", priority=25, config=config)
        self.appid = self.config.get("appid") or "Y7R353-9HQAAL8KKA"
        self.units = self.config.get("units") or "metric"
        self.session = CachedSession(backend="memory", expire_after=timedelta(minutes=5))

    # image api (simple)
    def get_image(self, query, context=None):
        url = 'http://api.wolframalpha.com/v1/simple'
        params = {"appid": self.appid,
                  "i": query,
                  "background": "F5F5F5",
                  "layout": "labelbar",
                  "units": self.units}
        path = join(tempfile.gettempdir(), query.replace(" ", "_")+".gif")
        if not isfile(path):
            image = self.session.get(url, params=params).content
            with open(path, "wb") as f:
                f.write(image)
        return path

    # spoken answers api (spoken)
    def get_spoken_answer(self, query, context):
        url = 'http://api.wolframalpha.com/v1/spoken'
        params = {"appid": self.appid,
                  "i": query,
                  "units": self.units}
        answer = self.session.get(url, params=params).text
        bad_answers = ["no spoken result available",
                       "wolfram alpha did not understand your input"]
        if answer.lower().strip() in bad_answers:
            return None
        return answer
