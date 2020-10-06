# {{data.personal.name[lang]}} {{data.personal.surname[lang]}}

email: [{{data.personal.email}}](mailto:{{data.personal.email}})

site: [{{data.personal.site}}]({{data.personal.site}})

phone: {{data.personal.phone}}


## Work Experience

{% for job in data.work_experience|reverse %}

### {{job.position[lang]}} at {{job.organisation.name[lang]}}
{{job.from_date}} - {% if job.current %}Present{% else %}{{job.to_date}}{% endif %}
{% for bullet in job.bullets %}
- {{bullet[lang]}}
{% endfor %}

{% if job.technologies %}
Key skills: {{job.technologies | join(", ")}}
{% endif %}

{% endfor %}

## Education

{% for education in data.education|reverse %}
### {{education.university[lang]}} / {{education.faculty[lang]}}
{{education.speciality[lang]}}
{% endfor %}
