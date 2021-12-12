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
import tempfile
from datetime import timedelta
from os.path import join, isfile

from neon_solvers import AbstractSolver
from requests_cache import CachedSession


class WolframAlphaSolver(AbstractSolver):
    def __init__(self, config=None):
        super(WolframAlphaSolver, self).__init__(name="WolframAlpha", priority=25, config=config)
        self.appid = self.config.get("appid") or "Y7R353-9HQAAL8KKA"
        self.units = self.config.get("units") or "metric"
        self.session = CachedSession(backend="memory", expire_after=timedelta(minutes=5))

    # data api
    def get_data(self, query, context=None):
        """
       query assured to be in self.default_lang
       return a dict response
       """
        url = 'http://api.wolframalpha.com/v2/query'
        params = {"appid": self.appid,
                  "input": query,
                  "output": "json",
                  "units": self.units}
        return self.session.get(url, params=params).json()

    # image api (simple)
    def get_image(self, query, context=None):
        """
        query assured to be in self.default_lang
        return path/url to a single image to acompany spoken_answer
        """
        url = 'http://api.wolframalpha.com/v1/simple'
        params = {"appid": self.appid,
                  "i": query,
                  # "background": "F5F5F5",
                  "layout": "labelbar",
                  "units": self.units}
        path = join(tempfile.gettempdir(), query.replace(" ", "_") + ".gif")
        if not isfile(path):
            image = self.session.get(url, params=params).content
            with open(path, "wb") as f:
                f.write(image)
        return path

    # spoken answers api (spoken)
    def get_spoken_answer(self, query, context):
        """
        query assured to be in self.default_lang
        return a single sentence text response
        """
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

    def get_expanded_answer(self, query, context=None):
        """
        query assured to be in self.default_lang
        return a list of ordered steps to expand the answer, eg, "tell me more"

        {
            "title": "optional",
            "summary": "speak this",
            "img": "optional/path/or/url
        }

        """
        data = self.get_data(query, context)
        # these are returned in spoken answer or otherwise unwanted
        skip = ['Input interpretation', 'Interpretation',
                'Result', 'Value', 'Image']
        steps = []

        for pod in data['queryresult']['pods']:
            title = pod["title"]
            if title in skip:
                continue

            for sub in pod["subpods"]:
                subpod = {"title": title}
                summary = sub["img"]["alt"]
                subtitle = sub["img"]["title"]
                if subtitle and subtitle != summary:
                    subpod["title"] = subtitle

                if summary == title:
                    # it's an image result
                    subpod["img"] = sub["img"]["src"]
                elif summary.startswith("(") and summary.endswith(")"):
                    continue
                else:
                    subpod["summary"] = summary
                steps.append(subpod)

        # do any extra processing here
        prev = ""
        for idx, step in enumerate(steps):
            # merge steps
            if step["title"] == prev:
                summary = steps[idx-1]["summary"] + "\n" + step["summary"]
                steps[idx]["summary"] = summary
                steps[idx]["img"] = step.get("img") or steps[idx -1 ]["img"]
                steps[idx-1] = None
            elif step.get("summary"):
                # inject title in speech, eg we do not want wolfram to just read family names without context
                steps[idx]["summary"] = step["title"] + "\n." + step["summary"]

            prev = step["title"]
        return [s for s in steps if s]


