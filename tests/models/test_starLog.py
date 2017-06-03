from unittest import TestCase

import pytest

from project.models import StarLog


@pytest.mark.usefixtures("session", 'db')
class TestStarLog(object):

    def test_add_to_starlog(self, session, db):
        s = StarLog(
                    "000000fb315c6d9bcee6e83606695ae2b"
                    "4a09beb929ce471608829c7273f8383",
                    0,
                    0,
                    0,
                    "000000000000000000000000000000000000000000000000"
                    "00000000000000000486604799146b10804b882971dbd"
                    "fe280cd516a704a7aac335493f8f906"
                    "1702dade7d2fe9149651025718078865",
                    0,
                    "000000000000000000000000000000000"
                    "0000000000000000000000000000000",
                    486604799,
                    18078865,
                    1496510257,
                    "a4c0eaed4cd7bf6c4283401d7cfdfd193"
                    "690bb6c01c87c7711d9ff6e49edf702",
                    0,
                    0,
                    0)
        session.add(s)
        session.commit()
        log = session.query(StarLog).order_by(StarLog.time.desc())\
            .first()
        assert log.hash == "000000fb315c6d9bcee6e83606695ae2" \
                           "b4a09beb929ce471608829c7273f8383"

    def test_get_json(self, session, db):
        s = StarLog("000000fb315c6d9bcee6e83606695ae2"
                    "b4a09beb929ce471608829c7273f8383",
                    0,
                    0,
                    0,
                    "00000000000000000000000000000000"
                    "00000000000000000000000000000000"
                    "0486604799146b10804b882971dbdfe2"
                    "80cd516a704a7aac335493f8f9061702"
                    "dade7d2fe9149651025718078865",
                    0,
                    "00000000000000000000000000000000"
                    "00000000000000000000000000000000",
                    486604799,
                    18078865,
                    1496510257,
                    "a4c0eaed4cd7bf6c4283401d7cfdfd19"
                    "3690bb6c01c87c7711d9ff6e49edf702",
                    0,
                    0,
                    0)
        session.add(s)
        session.commit()
        log = session.query(StarLog).order_by(StarLog.time.desc()).first()
        assert log.hash == "000000fb315c6d9bcee6e83606695ae" \
                           "2b4a09beb929ce471608829c7273f8383"
        assert log.log_header == "000000000000000000000000000" \
                                 "000000000000000000000000000" \
                                 "00000000000486604799146b108" \
                                 "04b882971dbdfe280cd516a704a" \
                                 "7aac335493f8f9061702dade7d2" \
                                 "fe9149651025718078865"
