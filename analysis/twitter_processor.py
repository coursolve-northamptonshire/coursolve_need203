""" Utility Class/es for doing post-processing on twitter data we collect
"""
import json
import pandas as pd
import numpy as np
import logging

LOG = logging.getLogger(__name__)


class Processor(object):
    '''Post Processing for twitter results.
    '''

    def __init__(self):
        pass

    def simple_results_iterator(self, fp, max=1000):
        '''A generator for iterating through the twitter results file.
        By default, iterates only through first 1000 valid lines
        if file contains an error, fails silently, but logs an error
        '''
        lines = 0
        errors = 0
        while lines < max:

            try:
                next_line = fp.readline()
                lines += 1
            except:
                errors += 1
                LOG.exception("Error reading file")
                continue

            if next_line is None:
                LOG.error("Unexpected file truncation at line %d", lines)
                break

            next_line = next_line.strip()

            if next_line == "":
                errors += 1
                LOG.warn("Skipping empty line at %d", lines)
                continue

            try:
                result = json.loads(next_line)
                yield result
            except ValueError:
                errors += 1
                LOG.warn("Unable to parse Line %d: %s", lines, next_line)
                continue
            except:
                errors += 1
                LOG.exception("Error reading JSON")
                continue

        LOG.error("Encountered %d errors while reading " +
                  "twitter results", errors)

    def make_result_rows(self, fp, results_iterator, max_rows):
        '''A generator to yield dicts as rows as input to the DataFrame constructor

        this is a helper function to quickly build a dataframe from a
        results file of twitter searches encoded in JSON.
        '''
        for result in results_iterator(fp, max_rows):
            text = result["text"]
            # print(text)
            # print(r["geo"])
            if "geo" in result and result["geo"] is None:
                (xlon, ylat) = (np.nan, np.nan)
            else:
                xlon = result["geo"]["coordinates"][0]
                ylat = result["geo"]["coordinates"][1]
            created_at = result["created_at"]
            tid = result["id"]
            user = "@" + result["user"]["screen_name"]

            d_row = {
                "id": tid,
                "status": text,
                "user": user,
                "created_at": created_at,
                "latitude": xlon,
                "longitude": ylat,
            }

            yield d_row

    def make_df(self, results_file, max_rows=1000):
        '''Make dataframe from results file
        '''
        try:
            dataframe = pd.DataFrame(self.make_result_rows(results_file,
                                                           self.simple_results_iterator,
                                                           max_rows))
        except:
            LOG.exception("Error creating dataframe")
            return None

        return dataframe
