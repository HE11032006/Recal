"""Catalogue de domaines sources par type d’opportunité.

Liste initiale générique, ajustable via `WatchSettings.allowed_domains`.
Une liste vide dans `WatchSettings.allowed_domains` désactive le filtrage.
Règle : priorité aux pages officielles, deadlines vérifiables, URL canonique.
"""

from __future__ import annotations

from urllib.parse import urlparse

from recal.domain.entities import OpportunityType

# Agrégateurs tout-en-un (bourses, stages, fellowships, conférences) :
# sources de découverte valables quel que soit le type surveillé.
SHARED_AGGREGATORS: list[str] = [
    "youthop.com",
    "opportunitydesk.org",
    "opportunitiescorners.info",
    "polenexus.com",
    "opportunitiesforyouth.org",
    "opportunitiescircle.com",
]

DEFAULT_DOMAIN_CATALOG: dict[str, list[str]] = {
    OpportunityType.HACKATHON.value: [
        "brabble.ai",
        "devpost.com",
        "mlh.io",
        "hackathon.com",
        "devfolio.co",
        "zindi.africa",
        "kaggle.com",
        "ethglobal.com",
        "hackclub.com",
        "unstop.com",
        "lablab.ai",
        "hackathons.space",
        "ushackathons.com",
        "allhackathons.com",
    ],
    OpportunityType.INTERNSHIP.value: [
        "linkedin.com",
        "indeed.com",
        "glassdoor.com",
        "internshala.com",
        "wellfound.com",
        "relocate.me",
        "remoteok.com",
        "weworkremotely.com",
        "amazon.jobs",
        "careers.microsoft.com",
        "careers.un.org",
        "app.unv.org",
        "euraxess.ec.europa.eu",
        "handshake.com",
        "buildyourfuture.withgoogle.com",
        "welcometothejungle.com",
        "jobteaser.com",
    ],
    OpportunityType.FELLOWSHIP.value: [
        "fellowship.mlh.com",
        "mlh.io",
        "summerofcode.withgoogle.com",
        "outreachy.org",
        "mentorship.lfx.linuxfoundation.org",
        "lfxmentorship.cncf.io",
        "profellow.com",
        "africanleadershipacademy.org",
        "echoinggreen.org",
        "millenniumfellows.org",
        "linkedin.com",
    ],
    OpportunityType.SCHOLARSHIP.value: [
        "linkedin.com",
        "campusfrance.org",
        "eacea.ec.europa.eu",
        "education.ec.europa.eu",
        "chevening.org",
        "daad.de",
        "foreign.fulbrightonline.org",
        "fulbrightonline.org",
        "educanada.ca",
        "cscuk.fcdo.gov.uk",
        "mastercardfdn.org",
        "scholarshippositions.com",
        "wemakescholars.com",
        "findamasters.com",
        "studyportals.com",
    ],
    OpportunityType.CONFERENCE.value: [
        "confs.tech",
        "sessionize.com",
        "dev.events",
        "10times.com",
        "eventbrite.com",
        "meetup.com",
        "lu.ma",
        "events.ieee.org",
        "acm.org",
        "pydata.org",
        "owasp.org",
        "djangoproject.com",
        "africatechsummit.com",
        "unstop.com",
    ],
    OpportunityType.CERTIFICATION.value: [
        "learn.microsoft.com",
        "netacad.com",
        "grow.google",
        "skillsbuild.org",
        "skillbuilder.aws",
        "freecodecamp.org",
        "cisco.com",
        "training.fortinet.com",
        "isc2.org",
        "coursera.org",
        "edx.org",
        "training.linuxfoundation.org",
        "buildyourfuture.withgoogle.com",
    ],
    OpportunityType.OTHER.value: [
        "opportunitiesforyouth.org",
        "opportunitiescircle.com",
    ],
}


def default_allowed_domains(opportunity_types: list[str]) -> list[str]:
    """Domaines par défaut pour les types demandés, sans doublon.

    Les agrégateurs transverses sont toujours inclus : ce sont des
    sources de découverte valables pour tous les types.
    """
    domains: list[str] = []
    for opportunity_type in opportunity_types:
        domains.extend(DEFAULT_DOMAIN_CATALOG.get(opportunity_type, []))
    domains.extend(SHARED_AGGREGATORS)
    return list(dict.fromkeys(domains))


def is_url_allowed(url: str, allowed_domains: list[str]) -> bool:
    """Vérifier qu’une URL appartient à un domaine autorisé (suffixe exact)."""
    if not allowed_domains:
        return True
    try:
        hostname = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    if not hostname:
        return False
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in allowed_domains)
