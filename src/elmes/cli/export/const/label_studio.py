"""Label Studio export constants."""

from typing import Sequence

from elmes.config.eval import EvalField


TEMPLATE_PREFIX = """<View>
  <Style>
    .container {
      display: flex;
      justify-content: space-between;
      margin: 0 auto;
      padding: 20px;
      background-color: #ffffff;
      border-radius: 5px;
      box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.1), 0 6px 20px 0 rgba(0, 0, 0, 0.1);
      max-width: 800px;
    }

    .border {
      border-style: solid;
    }

    .text-block {
      flex: 1;
      margin-right: 20px;
    }

    .assessment-items-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .assessment-item {
      background-color: rgba(44, 62, 80, 0.6);
      padding: 1px;
      border-radius: 5px;
      box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.1), 0 3px 10px 0 rgba(0, 0, 0, 0.1);
      color: #ffffff;
      word-wrap: break-word;
    }
  </Style>
  <View className="container">
    <View className="text-block">
      <Paragraphs name="dialogue" value="$messages" layout="dialogue" nameKey="role" textKey="content" />
    </View>
    <View className="assessment-item-container">
"""

TEMPLATE_SUFFIX = """
    </View>
  </View>
</View>
"""


def _generate_field_component(field: EvalField, name: str) -> str:
    """Generate a Label Studio component for a single field."""
    template = (
        f'<Header value="{name}" size="8"/><View className="assessment-item">%s</View>'
    )

    if field.type == "int":
        max_rating = field.max if field.max is not None else 5
        return (
            template
            % f'<Rating name="{name}" maxRating="{max_rating}" toName="dialogue" />'
        )
    elif field.type == "float":
        max_val = f' max="{field.max}"' if field.max is not None else ""
        return template % f'<Number name="{name}" toName="dialogue"{max_val} />'
    elif field.type == "str":
        return template % f'<TextArea name="{name}" toName="dialogue" />'
    elif field.type == "bool":
        return template % (
            f'<Choices name="{name}" toName="dialogue" showInline="true" choice="single-radio">'
            f'<Choice value="Yes"/><Choice value="No"/></Choices>'
        )
    elif field.type == "dict" and field.fields:
        children = generate_labeling(field.fields)
        return template % f'<View className="border">{children}</View>'
    else:
        raise NotImplementedError(f"Field type {field.type} not supported")


def generate_labeling(fields: Sequence[EvalField]) -> str:
    """Generate Label Studio components for evaluation fields."""
    components: list[str] = []
    for field in fields:
        name = field.name
        template = (
            f'<Header value="{name}" size="8"/>'
            f'<View className="assessment-item">'
            f'<Rating name="{name}" toName="dialogue" />'
        )
        if field.reason:
            template += f'<TextArea name="{name}_reason" toName="dialogue" placeholder="评分理由" />'
        template += "</View>"
        components.append(template)
    return "".join(components)


def generate_label_studio_interface(fields: Sequence[EvalField]) -> str:
    """Generate complete Label Studio interface XML."""
    return TEMPLATE_PREFIX + generate_labeling(fields) + TEMPLATE_SUFFIX
