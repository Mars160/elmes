from typing import Sequence
from elmes.entity import FormatField


TEMPLATE_template = """<View>
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


def generate_labeling(fields: Sequence[FormatField]) -> str:
    compoents: list[str] = []
    for field in fields:
        name = field.field
        template = f'      <Header value="{name}" size="8"/><View className="assessment-item">%s</View>\n'
        if field.type == "int":
            if field.max is not None:
                compoents.append(template % f'<Rating name="{name}" maxRating="{field.max}" toName="dialogue" />')
            else:
                compoents.append(template % f'<Rating name="{name}" maxRating="5" toName="dialogue" />')
        elif field.type == "float":
            if field.max is not None:
                compoents.append(template % f'<Number name="{name}" toName="dialogue" max="{field.max}" />')
            else:
                compoents.append(template % f'<Number name="{name}" toName="dialogue" />')
        elif field.type == "str":
            compoents.append(template % f'<TextArea name="{name}" toName="dialogue" />')
        elif field.type == "bool":
            compoents.append(template % f'<Choices name="{name}" toName="dialogue" showInline="true" choice="single-radio"><Choice value="Yes"/><Choice value="No"/></Choices>')
        elif field.type == "dict":
            children = generate_labeling(field.items)
            compoents.append(template % f'<View className="border">{"".join(children)}</View>')
        else:
            raise NotImplementedError
    return "".join(compoents)

def generate_label_studio_interface(fields: Sequence[FormatField]) -> str:
    return TEMPLATE_template + generate_labeling(fields) + TEMPLATE_SUFFIX

    
            
        
