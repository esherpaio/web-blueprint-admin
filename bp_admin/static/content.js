(function () {
    "use strict";

    const INLINE_TOOLBAR = ["bold", "italic", "link"];
    const EMBED_SERVICES = {
        youtube: {
            title: "YouTube",
            icon: '<i class="bi bi-youtube"></i>',
            hint: "Paste a YouTube video link",
        },
        instagram: {
            title: "Instagram",
            icon: '<i class="bi bi-instagram"></i>',
            hint: "Paste an Instagram post link",
        },
    };

    // Built on demand so a failed plugin CDN load can't break the rest of the admin bundle.
    function buildTools(uploadUrl) {
        class ListTool extends EditorjsList {
            renderSettings() {
                // The renderer has no custom counters or checklists.
                return super.renderSettings().slice(0, 2);
            }
        }

        class EmbedTool extends Embed {
            static get toolbox() {
                return Object.entries(EMBED_SERVICES).map(function ([service, { title, icon }]) {
                    return { title, icon, data: { service } };
                });
            }

            render() {
                if (!this.data.service || this.data.embed) return super.render();
                const input = document.createElement("input");
                input.className = "form-control";
                input.placeholder = EMBED_SERVICES[this.data.service].hint;
                input.addEventListener("paste", (event) => {
                    event.preventDefault();
                    this.embedLink(event.clipboardData.getData("text"));
                });
                input.addEventListener("keydown", (event) => {
                    if (event.key !== "Enter") return;
                    event.preventDefault();
                    event.stopPropagation();
                    this.embedLink(input.value);
                });
                this.element = input;
                return input;
            }

            validate(data) {
                return Boolean(data.embed);
            }

            embedLink(url) {
                this.onPaste({ detail: { key: this.data.service, data: url.trim() } });
                if (this.data.embed) return;
                this.api.notifier.show({ message: "This link is not supported.", style: "error" });
            }
        }

        return {
            paragraph: { inlineToolbar: INLINE_TOOLBAR },
            header: { class: Header, config: { levels: [2, 3], defaultLevel: 2 } },
            list: {
                class: ListTool,
                inlineToolbar: INLINE_TOOLBAR,
                toolbox: [{ title: "Bullet list" }, { title: "Numbered list" }],
            },
            image: {
                class: ImageTool,
                config: {
                    endpoints: { byFile: uploadUrl },
                    field: "file",
                    features: { border: false, background: false, stretch: false, caption: "optional" },
                },
            },
            embed: { class: EmbedTool, config: { services: { youtube: true, instagram: true } } },
            attaches: {
                class: AttachesTool,
                toolbox: { title: "Download" },
                config: { endpoint: uploadUrl, field: "file" },
            },
        };
    }

    function initContentEditor() {
        const holder = document.querySelector("[data-content-editor]");
        if (!holder) return;
        const config = JSON.parse(holder.dataset.contentEditor);
        const tools = buildTools(config.uploadUrl);
        const editor = new EditorJS({
            holder,
            data: config.data,
            placeholder: "Start writing, or click + to add content",
            minHeight: 32,
            tools: Object.fromEntries(
                config.tools.map(function (name) {
                    return [name, tools[name]];
                }),
            ),
        });
        editor.isReady.catch(function () {
            window.adminFlash("The editor could not load. Reload this page before editing.");
        });

        document.querySelectorAll("[data-content-form]").forEach(function (form) {
            form.addEventListener("submit", async function (event) {
                event.preventDefault();
                const button = event.submitter;
                button.disabled = true;
                try {
                    await editor.isReady;
                    form.elements.content.value = JSON.stringify(await editor.save());
                    form.submit();
                } catch (error) {
                    window.adminFlash("Content could not be saved. Please try again.");
                } finally {
                    button.disabled = false;
                }
            });
        });
    }

    window.addEventListener("load", initContentEditor);
})();
