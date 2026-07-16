import DOMPurify from 'dompurify'

export function string_to_html(string = '') {
  string = String(string)
  let urls = string.match(/https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)/g)
  if (urls !== null) {
    for (let url of urls) {
      let text;
      const subUrl = url.split("\/\/")[1]
      if (url.includes("docs.google.com")) {
        text = "google-" + subUrl.split("\/")[1]
      } else if (url.includes("trello.com")) {
        text = "trello-" + subUrl.split("\/").pop()
      } else if (url.includes("github.com")) {
        text = "gh-" + subUrl.split("\/")[1] + "-" + subUrl.split("\/")[2]
      } else {
        text = url.split("\/\/")[1].split("\/")[0]
      }
      string = string.replace(url, "<a href=\"" + url + "\" target=\"_blank\" rel=\"noopener noreferrer\">" + text + "</a>")
    }
  }

  string = string.replaceAll('\n', "<br>")

  let bolds = string.match(/\*[^*]*\*/g)
  if (bolds !== null) {
    for (let bold of bolds) {
      string = string.replace(bold, bold.replace("*", "<b>").replace("*", "</b>"))
    }
  }

  let strikes = string.match(/\^[^*]*\^/g)
  if (strikes !== null) {
    for (let strike of strikes) {
      string = string.replace(strike, strike.replace("^", "<s>").replace("^", "</s>"))
    }
  }

  return DOMPurify.sanitize(string, {
    ALLOWED_TAGS: ['a', 'b', 'br', 's'],
    ALLOWED_ATTR: ['href', 'rel', 'target'],
  })
}

export function compareDates(a, b) {
  return a.localeCompare(b)
}

export function formatDate(date) {
  if (!date) return ''
  const parsedDate = new Date(`${date}T00:00:00Z`)
  if (Number.isNaN(parsedDate.getTime())) return date
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'UTC',
  }).format(parsedDate)
}
