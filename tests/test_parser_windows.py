"""Unit tests for the Windows Event Log XML parser."""

from parser.formats.windows import parse_windows_xml

_EVENT_4672 = """<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <EventID>4672</EventID>
    <TimeCreated SystemTime="2026-06-29T10:10:00.000Z"/>
    <Computer>DESKTOP-CORP01</Computer>
  </System>
  <EventData>
    <Data Name="SubjectUserName">jdupont</Data>
    <Data Name="SubjectDomainName">CORP</Data>
    <Data Name="PrivilegeList">SeDebugPrivilege</Data>
  </EventData>
</Event>"""

_EVENT_4720 = """<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <EventID>4720</EventID>
    <TimeCreated SystemTime="2026-06-29T10:12:00.000Z"/>
    <Computer>DESKTOP-CORP01</Computer>
  </System>
  <EventData>
    <Data Name="SubjectUserName">administrator</Data>
    <Data Name="TargetUserName">hackeruser</Data>
  </EventData>
</Event>"""

_EVENT_4657_SAM = """<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <EventID>4657</EventID>
    <TimeCreated SystemTime="2026-06-29T10:15:00.000Z"/>
    <Computer>DESKTOP-CORP01</Computer>
  </System>
  <EventData>
    <Data Name="SubjectUserName">SYSTEM</Data>
    <Data Name="ObjectName">\\REGISTRY\\MACHINE\\SAM\\SAM\\Domains</Data>
  </EventData>
</Event>"""


def test_event_4672_privilege_assigned():
    event = parse_windows_xml(_EVENT_4672)
    assert event is not None
    assert event.action == "privilege_assigned"
    assert event.user == "jdupont"
    assert event.source_type == "windows"
    assert event.source_ip is None
    assert "T" in event.timestamp
    assert _EVENT_4672 == event.raw_log


def test_event_4720_account_created():
    event = parse_windows_xml(_EVENT_4720)
    assert event is not None
    assert event.action == "user_account_created"
    # TargetUserName preferred over SubjectUserName for creation events
    assert event.user == "hackeruser"


def test_event_4657_registry():
    event = parse_windows_xml(_EVENT_4657_SAM)
    assert event is not None
    assert event.action == "registry_value_modified"
    assert event.user == "SYSTEM"


def test_malformed_xml_returns_none():
    assert parse_windows_xml("<Event><broken") is None


def test_empty_returns_none():
    assert parse_windows_xml("") is None
