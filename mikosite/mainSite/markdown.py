from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension


class ReplaceHeadersProcessor(Treeprocessor):
    def run(self, root):
        for element in root.iter():
            if element.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                element.tag = 'p'
        return root


class DisallowHeadersExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(ReplaceHeadersProcessor(md), 'disallow_headers', 175)
