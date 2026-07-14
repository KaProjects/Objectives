import DOMPurify from 'dompurify'

export function string_to_html(string = ''){
    string = String(string)
    let urls = string.match(/https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)/g)
    if (urls !== null) {
        for (let url of urls){
            let text;
            const subUrl = url.split("\/\/")[1]
            if (url.includes("docs.google.com")){
                text = "google-" + subUrl.split("\/")[1]
            } else if (url.includes("trello.com")){
                text = "trello-" + subUrl.split("\/").pop()
            } else if (url.includes("github.com")){
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
        for (let bold of bolds){
            string = string.replace(bold, bold.replace("*","<b>").replace("*","</b>"))
        }
    }

    let strikes = string.match(/\^[^*]*\^/g)
    if (strikes !== null) {
        for (let strike of strikes){
            string = string.replace(strike, strike.replace("^","<s>").replace("^","</s>"))
        }
    }

    return DOMPurify.sanitize(string, {
        ALLOWED_TAGS: ['a', 'b', 'br', 's'],
        ALLOWED_ATTR: ['href', 'rel', 'target'],
    })
}
export function compare_dates(a, b){
    let dateA = a.split("/")
    let dateB = b.split("/")
    if (dateA[2] !== dateB[2]){
        return parseInt(dateA[2]) - parseInt(dateB[2])
    } else {
        if (dateA[1] !== dateB[1]) {
            return parseInt(dateA[1]) - parseInt(dateB[1])
        } else {
            if (dateA[0] !== dateB[0]) {
                return parseInt(dateA[0]) - parseInt(dateB[0])
            } else {
                return 0
            }
        }
    }
}
