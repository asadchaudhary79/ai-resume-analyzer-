"""Test parser with sample resume text (run: pytest tests/test_parser_sample.py -v)."""
import pytest
from app.services.pdf_parser import parse_structured_data

SAMPLE_TEXT = """
Muhammad Asad Mushtaq
Software Engineer / Full Stack Developer
asadchoudhary79@gmail.com 03458707507 Johar town Lahore,Pakistan, 54000 Lahore
April 3, 1998 Pakistan Married linkedin.com/in/asadchaudhary79
I am an experienced full-stack developer with over 5 years of expertise in utilizing cutting-edge technologies such as
WordPress, Php , Laravel, VueJS, and React for web application development.
Area of Strength Excellent communications, Strong in reconciling problems and
interpersonal and leadership skills. resolve conflict.
Education
Mar 2019 - Feb 2021 MCS: Master of Computer Science
University of managment & technology, lahore
Experience
Mar 2019 - Present Freelancer Wordpress/Web Developer
Fiver & Upwork, Lahore
Feb 2020 - Apr 2022 Senior WordPress & PHP Developer
Hashmaker Solutions, Lahore
Strengths & Skills HTML/CSS/BootStrap WordPress
JavaScript jQuery
Laravel Framework Core Php
Theme Development Plugin Development
WordPress Headless React Js
Vue JS Shopify Development
Languages English Urdu
Punjabi
Projects Business Website
business2sell
https://www.servicebull.com/
Certificates
Feb 2020 WordPress Headleass
Programming Language: javeScript,HTML5, Css, PHP , React
"""


def test_parser_extracts_skills_education_experience():
    data = parse_structured_data(SAMPLE_TEXT)
    assert data["name"] == "Muhammad Asad Mushtaq"
    assert data["email"] == "asadchoudhary79@gmail.com"
    assert data["phone"] == "03458707507"
    assert len(data["skills"]) > 0, "Skills should be parsed (HTML, WordPress, Laravel, etc.)"
    assert len(data["education"]) > 0, "Education should be parsed"
    assert len(data["experience"]) > 0, "Experience should be parsed"
    assert len(data["projects"]) > 0, "Projects should be parsed"
    assert len(data["certifications"]) > 0, "Certifications should be parsed"
    assert len(data["languages"]) > 0, "Languages should be parsed"
