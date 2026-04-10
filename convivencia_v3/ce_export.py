"""Respuestas de descarga CSV (UTF-8 con BOM para Excel)."""
import csv
from io import BytesIO

from flask import Response


def csv_response(filename, header, rows):
    """
    header: list[str]
    rows: iterable[list|tuple] con la misma longitud que header
    """

    def gen():
        out = BytesIO()
        out.write(b"\xef\xbb\xbf")
        txt = out.getvalue().decode("utf-8", errors="ignore")
        yield txt
        out = BytesIO()
        w = csv.writer(out, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        w.writerow(header)
        yield out.getvalue().decode("utf-8", errors="ignore")
        for r in rows:
            out = BytesIO()
            w = csv.writer(out, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
            w.writerow(list(r))
            yield out.getvalue().decode("utf-8", errors="ignore")

    return Response(
        gen(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
