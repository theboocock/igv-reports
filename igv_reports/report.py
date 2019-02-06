import os
import sys
import json
import math
import argparse
from urllib.request import urlopen
from igv_reports import fasta, ideogram, datauri, tracks
from igv_reports.variant_table import VariantTable
from igv_reports.bed_table import BedTable

def create_report(args):

    variants_file = args.variants

    if variants_file.endswith(".vcf") or variants_file.endswith (".vcf.gz"):
        info_columns = args.infoColumns.split(",") if args.infoColumns else None
        table = VariantTable(variants_file, info_columns)

    elif variants_file.endswith(".bed") or variants_file.endswith(".bed.gz"):
        table = BedTable(variants_file)

    table_json = table.to_JSON()

    session_dict = {}

    # loop through variants creating an igv.js session for each one
    for tuple in table.features:

        feature = tuple[0]
        unique_id = tuple[1]

        # Define a genomic region around the variant
        chr = feature.chr
        position = int(math.floor((feature.start + feature.end) / 2)) + 1   # center of region in 1-based coordinates
        start = int (math.floor(feature.start - int(args.flanking) / 2))
        end = int (math.ceil(feature.end + int(args.flanking) / 2))
        region = {
            "chr": chr,
            "start": start,
            "end": end
        }

        # Fasta
        data = fasta.get_data(args.fasta, region)
        fa = '>' + chr + ':' + str(start) + '-' + str(end) + '\n' + data
        fasta_uri = datauri.get_data_uri(fa)
        fastaJson = {
            "fastaURL": fasta_uri,
        }

        # Ideogram
        if(args.ideogram):
            ideo_string = ideogram.get_data(args.ideogram, region)
            ideo_uri = datauri.get_data_uri(ideo_string)
            fastaJson["cytobandURL"] = ideo_uri


        # Initial locus, +/- 20 bases
        initial_locus = chr + ":" + str(position - 20) + "-" + str(position + 20)
        session_json = {
            "locus": initial_locus,
            "reference": fastaJson,
            "tracks": []
        }

        if (args.tracks):
            trackList = args.tracks.split(',')
            for track in trackList:
                trackObj = tracks.get_track_json_dict(track)
                trackObj["url"] = datauri.file_to_data_uri(track, trackObj['format'], region)


                if(trackObj["type"] == "alignment"):
                    trackObj["height"] = 500

                # Sort TODO -- do this only for SNV
                # if (trackObj["type"]) == "alignment":
                #     trackObj["sort"] = {
                #         "option": "NUCLEOTIDE",
                #         "locus": chr + ":" + str(variant.pos - 1)
                #     }

                session_json["tracks"].append(trackObj)


        # Build the session data URI

        session_string = json.dumps(session_json);

        session_uri = datauri.get_data_uri(session_string)

        session_dict[str(unique_id)] = session_uri

    session_dict = json.dumps(session_dict)

    template_file = args.template
    if None == template_file:
        template_file = os.path.dirname(sys.modules['igv_reports'].__file__) + '/templates/variant_template.html'

    output_file = args.output

    standalone = args.standalone
    with open(template_file, "r") as f:
        data = f.readlines()

        with open(output_file, "w") as o:

            for i, line in enumerate(data):

                if standalone and line.find("<script") and line.find(".js") > 0:
                    print(inline_script(line, o))

                else:
                    j = line.find('"@TABLE_JSON@"')
                    if j >= 0:
                        line = line.replace('"@TABLE_JSON@"', table_json)

                    j = line.find('"@SESSION_DICTIONARY@"')
                    if j >= 0:
                        line = line.replace('"@SESSION_DICTIONARY@"', session_dict)

                    o.write(line)


def inline_script(line, o):
    #<script type="text/javascript" src="https://igv.org/web/test/dist/igv.min.js"></script>
    s = line.find('src="')
    if s > 0:
        e = line.find('">', s)
        url = line[s+5:e]

        response = urlopen(url)
        js = response.read().decode('utf-8')
        response.close()

        o.write('<script type="text/javascript">\n')
        o.write(js)
        o.write('</script>\n')



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("variants", help="vcf file defining variants, required")
    parser.add_argument("fasta", help="reference fasta file, required")
    parser.add_argument("--ideogram", help="ideogram file in UCSC cytoIdeo format")
    parser.add_argument("--tracks", help="comma-delimited list of track files")
    parser.add_argument("--template", help="html template file", default=None)
    parser.add_argument("--output", help="output file name", default="igvjs_viewer.html")
    parser.add_argument("--infoColumns", help="comma delimited list of VCF info field names to include in variant table")
    parser.add_argument("--flanking", help="genomic region to include either side of variant", default=1000)
    parser.add_argument('--standalone', help='Print more data', action='store_true')
    args = parser.parse_args()
    create_report(args)

if __name__ == "__main__":

    main()
