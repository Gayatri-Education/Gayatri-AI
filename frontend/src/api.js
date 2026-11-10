export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    credentials: "same-origin",
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  if (!response.ok) {
    let data;
    try {
      data = await response.json();
    } catch {
      /* use status below */
    }
    const detail = data?.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((x) => x.msg).join("; ")
          : `Request failed (${response.status})`,
    );
  }
  return response.status === 204 ? null : response.json();
}
export const go = (path) => {
  window.location.hash = path;
};
