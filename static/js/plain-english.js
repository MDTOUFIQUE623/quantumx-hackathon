/** Plain-language helper text for judges and presenters. */

export function plainExample(text) {
  return `<div class="plain-example"><strong>In plain English:</strong> ${text}</div>`;
}

export function plainLabel(technical, simple) {
  return `${technical}<br /><span class="plain-inline">${simple}</span>`;
}
