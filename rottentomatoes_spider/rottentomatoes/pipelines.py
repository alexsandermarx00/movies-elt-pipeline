import re

from itemadapter import ItemAdapter

_CTRL_RE = re.compile(r"[\x00-\x1f]")


class RottentomatoesPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        for key in adapter.field_names():
            value = adapter[key]
            if isinstance(value, str):
                adapter[key] = _CTRL_RE.sub(" ", value)
        return item
