"""Stable component identifiers for the Elasticity workflow page."""

from __future__ import annotations


class ElasticityIds:
    """Namespace of IDs shared by the page and callback modules."""

    FORM_HOST = "q-elasticity-form-host"
    IMPORT_STATUS = "q-elasticity-import-status"
    SOURCE = "q-elasticity-source"
    SESSION = "q-elasticity-session"
    EVENTS = "q-elasticity-events"
    POLL = "q-elasticity-poll"
    RUNTIME = "q-elasticity-runtime"
    ACTIVITY = "q-elasticity-activity"
    ACTIVITY_TABS = "q-elasticity-activity-tabs"
    ACTIVITY_OUTPUT = "q-elasticity-activity-output"
    SUMMARY = "q-elasticity-summary"
    CANCEL = "q-elasticity-cancel"
    BACK = "q-elasticity-back"
    OPEN_RESULTS = "q-elasticity-open-results"
    DOWNLOAD_HDF5 = "q-elasticity-download-hdf5"
    DOWNLOAD_HDF5_PAYLOAD = "q-elasticity-download-hdf5-payload"
    DOWNLOAD_REPORT = "q-elasticity-download-report"
    DOWNLOAD_REPORT_PAYLOAD = "q-elasticity-download-report-payload"
    DOWNLOAD_DIAGNOSTIC = "q-elasticity-download-diagnostic"
    DOWNLOAD_DIAGNOSTIC_PAYLOAD = "q-elasticity-download-diagnostic-payload"


__all__ = ["ElasticityIds"]
