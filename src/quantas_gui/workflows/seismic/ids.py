"""Stable component identifiers for the SEISMIC workflow page."""

from __future__ import annotations


class SeismicIds:
    """Namespace of IDs shared by the page and callback modules."""

    FORM_HOST = "q-seismic-form-host"
    IMPORT_STATUS = "q-seismic-import-status"
    SOURCE = "q-seismic-source"
    SESSION = "q-seismic-session"
    EVENTS = "q-seismic-events"
    POLL = "q-seismic-poll"
    RUNTIME = "q-seismic-runtime"
    ACTIVITY = "q-seismic-activity"
    ACTIVITY_TABS = "q-seismic-activity-tabs"
    ACTIVITY_OUTPUT = "q-seismic-activity-output"
    SUMMARY = "q-seismic-summary"
    CANCEL = "q-seismic-cancel"
    BACK = "q-seismic-back"
    OPEN_RESULTS = "q-seismic-open-results"
    DOWNLOAD_HDF5 = "q-seismic-download-hdf5"
    DOWNLOAD_HDF5_PAYLOAD = "q-seismic-download-hdf5-payload"
    DOWNLOAD_REPORT = "q-seismic-download-report"
    DOWNLOAD_REPORT_PAYLOAD = "q-seismic-download-report-payload"
    DOWNLOAD_CSV = "q-seismic-download-csv"
    DOWNLOAD_CSV_PAYLOAD = "q-seismic-download-csv-payload"
    DOWNLOAD_DIAGNOSTIC = "q-seismic-download-diagnostic"
    DOWNLOAD_DIAGNOSTIC_PAYLOAD = "q-seismic-download-diagnostic-payload"


__all__ = ["SeismicIds"]
