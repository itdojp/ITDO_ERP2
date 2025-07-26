"""Mobile SDK UI Components & Widgets Module - CC02 v72.0 Day 17."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from .mobile_sdk_core import MobileERPSDK


class ComponentType(str, Enum):
    """UI component types."""

    BUTTON = "button"
    INPUT = "input"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SWITCH = "switch"
    SLIDER = "slider"
    PROGRESS = "progress"
    ALERT = "alert"
    MODAL = "modal"
    CARD = "card"
    LIST = "list"
    TABLE = "table"
    CHART = "chart"
    FORM = "form"
    NAVIGATION = "navigation"
    TAB = "tab"
    ACCORDION = "accordion"
    CAROUSEL = "carousel"
    CALENDAR = "calendar"
    DATEPICKER = "datepicker"
    FILEPICKER = "filepicker"
    CAMERA = "camera"
    MAP = "map"
    WEBVIEW = "webview"


class ThemeMode(str, Enum):
    """Theme modes."""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class LayoutType(str, Enum):
    """Layout types."""

    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    GRID = "grid"
    FLEX = "flex"
    ABSOLUTE = "absolute"


class ComponentState(str, Enum):
    """Component states."""

    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"
    DISABLED = "disabled"


class ValidationRule(BaseModel):
    """Input validation rule."""

    rule_type: str  # required, minLength, maxLength, pattern, email, etc.
    value: Optional[Union[str, int, float]] = None
    message: str
    enabled: bool = True


class ComponentStyle(BaseModel):
    """Component styling configuration."""

    width: Optional[Union[str, int]] = None
    height: Optional[Union[str, int]] = None
    margin: Optional[Union[str, Dict[str, Union[str, int]]]] = None
    padding: Optional[Union[str, Dict[str, Union[str, int]]]] = None
    background_color: Optional[str] = None
    border_color: Optional[str] = None
    border_width: Optional[int] = None
    border_radius: Optional[int] = None
    text_color: Optional[str] = None
    font_size: Optional[int] = None
    font_weight: Optional[str] = None
    opacity: Optional[float] = None
    shadow: Optional[Dict[str, Any]] = None
    custom_css: Dict[str, str] = Field(default_factory=dict)


class ComponentProps(BaseModel):
    """Base component properties."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: ComponentType
    label: Optional[str] = None
    placeholder: Optional[str] = None
    value: Optional[Any] = None
    default_value: Optional[Any] = None
    disabled: bool = False
    readonly: bool = False
    required: bool = False
    visible: bool = True

    # Styling
    style: ComponentStyle = Field(default_factory=ComponentStyle)
    css_classes: List[str] = Field(default_factory=list)

    # Validation
    validation_rules: List[ValidationRule] = Field(default_factory=list)

    # Events
    on_change: Optional[str] = None  # JavaScript function name
    on_click: Optional[str] = None
    on_focus: Optional[str] = None
    on_blur: Optional[str] = None

    # Accessibility
    aria_label: Optional[str] = None
    aria_description: Optional[str] = None
    tab_index: Optional[int] = None

    # Data attributes
    data_attributes: Dict[str, str] = Field(default_factory=dict)

    # Custom properties
    custom_props: Dict[str, Any] = Field(default_factory=dict)


class ButtonProps(ComponentProps):
    """Button component properties."""

    type: ComponentType = ComponentType.BUTTON
    button_type: str = "primary"  # primary, secondary, danger, success, warning
    size: str = "medium"  # small, medium, large
    icon: Optional[str] = None
    icon_position: str = "left"  # left, right, only
    loading: bool = False
    submit: bool = False


class InputProps(ComponentProps):
    """Input component properties."""

    type: ComponentType = ComponentType.INPUT
    input_type: str = "text"  # text, password, email, number, tel, url
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    pattern: Optional[str] = None
    autocomplete: Optional[str] = None
    keyboard_type: Optional[str] = None  # Mobile specific
    secure_entry: bool = False  # Mobile specific


class DropdownProps(ComponentProps):
    """Dropdown component properties."""

    type: ComponentType = ComponentType.DROPDOWN
    options: List[Dict[str, Any]] = Field(default_factory=list)
    multiple: bool = False
    searchable: bool = False
    clearable: bool = False
    loading: bool = False
    remote_url: Optional[str] = None
    option_label_key: str = "label"
    option_value_key: str = "value"


class ListProps(ComponentProps):
    """List component properties."""

    type: ComponentType = ComponentType.LIST
    items: List[Dict[str, Any]] = Field(default_factory=list)
    item_template: Optional[str] = None
    selectable: bool = False
    multi_select: bool = False
    searchable: bool = False
    sortable: bool = False
    paginated: bool = False
    items_per_page: int = 20
    virtual_scrolling: bool = False


class TableProps(ComponentProps):
    """Table component properties."""

    type: ComponentType = ComponentType.TABLE
    columns: List[Dict[str, Any]] = Field(default_factory=list)
    data: List[Dict[str, Any]] = Field(default_factory=list)
    sortable: bool = True
    filterable: bool = True
    selectable: bool = False
    paginated: bool = True
    page_size: int = 10
    striped: bool = True
    bordered: bool = True
    compact: bool = False


class ChartProps(ComponentProps):
    """Chart component properties."""

    type: ComponentType = ComponentType.CHART
    chart_type: str = "line"  # line, bar, pie, doughnut, area, scatter
    data: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)
    responsive: bool = True
    animate: bool = True
    legend_position: str = "top"  # top, bottom, left, right, none


class FormProps(ComponentProps):
    """Form component properties."""

    type: ComponentType = ComponentType.FORM
    fields: List[ComponentProps] = Field(default_factory=list)
    layout: LayoutType = LayoutType.VERTICAL
    submit_url: Optional[str] = None
    method: str = "POST"
    validate_on_blur: bool = True
    validate_on_submit: bool = True
    show_validation_summary: bool = True


class ModalProps(ComponentProps):
    """Modal component properties."""

    type: ComponentType = ComponentType.MODAL
    title: Optional[str] = None
    size: str = "medium"  # small, medium, large, fullscreen
    closable: bool = True
    backdrop_dismiss: bool = True
    header_visible: bool = True
    footer_visible: bool = True
    buttons: List[ButtonProps] = Field(default_factory=list)
    content: Optional[str] = None


class NavigationProps(ComponentProps):
    """Navigation component properties."""

    type: ComponentType = ComponentType.NAVIGATION
    nav_type: str = "tabs"  # tabs, sidebar, drawer, breadcrumb
    items: List[Dict[str, Any]] = Field(default_factory=list)
    active_item: Optional[str] = None
    collapsible: bool = False
    position: str = "top"  # top, bottom, left, right


class Theme(BaseModel):
    """UI theme configuration."""

    name: str
    mode: ThemeMode = ThemeMode.LIGHT

    # Color palette
    primary_color: str = "#007AFF"
    secondary_color: str = "#5856D6"
    success_color: str = "#34C759"
    warning_color: str = "#FF9500"
    error_color: str = "#FF3B30"
    info_color: str = "#5AC8FA"

    # Background colors
    background_primary: str = "#FFFFFF"
    background_secondary: str = "#F2F2F7"
    background_tertiary: str = "#FFFFFF"

    # Text colors
    text_primary: str = "#000000"
    text_secondary: str = "#8E8E93"
    text_tertiary: str = "#C7C7CC"

    # Border colors
    border_primary: str = "#C6C6C8"
    border_secondary: str = "#E5E5EA"

    # Typography
    font_family_primary: str = "system-ui, -apple-system, sans-serif"
    font_family_monospace: str = "Monaco, Consolas, monospace"

    # Font sizes
    font_size_xs: int = 12
    font_size_sm: int = 14
    font_size_base: int = 16
    font_size_lg: int = 18
    font_size_xl: int = 20
    font_size_2xl: int = 24
    font_size_3xl: int = 30

    # Spacing
    spacing_xs: int = 4
    spacing_sm: int = 8
    spacing_base: int = 16
    spacing_lg: int = 24
    spacing_xl: int = 32
    spacing_2xl: int = 48

    # Border radius
    border_radius_sm: int = 4
    border_radius_base: int = 8
    border_radius_lg: int = 12
    border_radius_xl: int = 16

    # Shadows
    shadow_sm: str = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    shadow_base: str = "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)"
    shadow_lg: str = (
        "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
    )

    # Custom properties
    custom_properties: Dict[str, str] = Field(default_factory=dict)


class UIComponent(ABC):
    """Base UI component class."""

    def __init__(self, props: ComponentProps) -> dict:
        self.props = props
        self.state = ComponentState.IDLE
        self.validation_errors: List[str] = []

    @abstractmethod
    def render(self) -> Dict[str, Any]:
        """Render component to platform-specific format."""
        pass

    def validate(self) -> bool:
        """Validate component value."""
        self.validation_errors.clear()

        if self.props.required and not self.props.value:
            self.validation_errors.append("This field is required")
            return False

        for rule in self.props.validation_rules:
            if not rule.enabled:
                continue

            if not self._validate_rule(rule):
                self.validation_errors.append(rule.message)

        return len(self.validation_errors) == 0

    def _validate_rule(self, rule: ValidationRule) -> bool:
        """Validate single rule."""
        value = self.props.value

        if rule.rule_type == "required":
            return value is not None and str(value).strip() != ""
        elif rule.rule_type == "minLength":
            return len(str(value or "")) >= (rule.value or 0)
        elif rule.rule_type == "maxLength":
            return len(str(value or "")) <= (rule.value or float("inf"))
        elif rule.rule_type == "pattern":
            import re

            return bool(re.match(rule.value or "", str(value or "")))
        elif rule.rule_type == "email":
            import re

            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            return bool(re.match(email_pattern, str(value or "")))
        elif rule.rule_type == "number":
            try:
                float(value or 0)
                return True
            except ValueError:
                return False
        elif rule.rule_type == "min":
            try:
                return float(value or 0) >= (rule.value or 0)
            except ValueError:
                return False
        elif rule.rule_type == "max":
            try:
                return float(value or 0) <= (rule.value or float("inf"))
            except ValueError:
                return False

        return True

    def set_state(self, state: ComponentState) -> None:
        """Set component state."""
        self.state = state

    def set_value(self, value: Any) -> None:
        """Set component value."""
        self.props.value = value

    def get_value(self) -> Any:
        """Get component value."""
        return self.props.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary."""
        return {
            "id": self.props.id,
            "type": self.props.type.value,
            "props": self.props.dict(),
            "state": self.state.value,
            "validation_errors": self.validation_errors,
            "render_data": self.render(),
        }


class Button(UIComponent):
    """Button component."""

    def __init__(self, props: ButtonProps) -> dict:
        super().__init__(props)
        self.props: ButtonProps = props

    def render(self) -> Dict[str, Any]:
        """Render button component."""
        return {
            "element": "button",
            "attributes": {
                "id": self.props.id,
                "type": "submit" if self.props.submit else "button",
                "class": " ".join(
                    [
                        f"btn-{self.props.button_type}",
                        f"btn-{self.props.size}",
                        "btn-loading" if self.props.loading else "",
                        *self.props.css_classes,
                    ]
                ).strip(),
                "disabled": self.props.disabled or self.props.loading,
                **self.props.data_attributes,
            },
            "content": {
                "icon": self.props.icon,
                "icon_position": self.props.icon_position,
                "text": self.props.label,
                "loading": self.props.loading,
            },
            "events": {
                "onClick": self.props.on_click,
            },
            "style": self.props.style.dict(exclude_none=True),
        }


class Input(UIComponent):
    """Input component."""

    def __init__(self, props: InputProps) -> dict:
        super().__init__(props)
        self.props: InputProps = props

    def render(self) -> Dict[str, Any]:
        """Render input component."""
        return {
            "element": "input",
            "attributes": {
                "id": self.props.id,
                "type": self.props.input_type,
                "class": " ".join(
                    [
                        "form-input",
                        "invalid" if self.validation_errors else "",
                        *self.props.css_classes,
                    ]
                ).strip(),
                "value": self.props.value or "",
                "placeholder": self.props.placeholder,
                "disabled": self.props.disabled,
                "readonly": self.props.readonly,
                "required": self.props.required,
                "maxlength": self.props.max_length,
                "minlength": self.props.min_length,
                "pattern": self.props.pattern,
                "autocomplete": self.props.autocomplete,
                **self.props.data_attributes,
            },
            "mobile_attributes": {
                "keyboardType": self.props.keyboard_type,
                "secureTextEntry": self.props.secure_entry,
            },
            "events": {
                "onChange": self.props.on_change,
                "onFocus": self.props.on_focus,
                "onBlur": self.props.on_blur,
            },
            "validation": {
                "rules": [rule.dict() for rule in self.props.validation_rules],
                "errors": self.validation_errors,
            },
            "style": self.props.style.dict(exclude_none=True),
        }


class Dropdown(UIComponent):
    """Dropdown component."""

    def __init__(self, props: DropdownProps) -> dict:
        super().__init__(props)
        self.props: DropdownProps = props

    def render(self) -> Dict[str, Any]:
        """Render dropdown component."""
        return {
            "element": "select",
            "attributes": {
                "id": self.props.id,
                "class": " ".join(
                    [
                        "form-select",
                        "multiple" if self.props.multiple else "",
                        "searchable" if self.props.searchable else "",
                        *self.props.css_classes,
                    ]
                ).strip(),
                "multiple": self.props.multiple,
                "disabled": self.props.disabled,
                "required": self.props.required,
                **self.props.data_attributes,
            },
            "options": self.props.options,
            "selected_value": self.props.value,
            "config": {
                "searchable": self.props.searchable,
                "clearable": self.props.clearable,
                "loading": self.props.loading,
                "remote_url": self.props.remote_url,
                "label_key": self.props.option_label_key,
                "value_key": self.props.option_value_key,
            },
            "events": {
                "onChange": self.props.on_change,
            },
            "style": self.props.style.dict(exclude_none=True),
        }


class List(UIComponent):
    """List component."""

    def __init__(self, props: ListProps) -> dict:
        super().__init__(props)
        self.props: ListProps = props

    def render(self) -> Dict[str, Any]:
        """Render list component."""
        return {
            "element": "ul",
            "attributes": {
                "id": self.props.id,
                "class": " ".join(
                    [
                        "component-list",
                        "selectable" if self.props.selectable else "",
                        "multi-select" if self.props.multi_select else "",
                        *self.props.css_classes,
                    ]
                ).strip(),
                **self.props.data_attributes,
            },
            "items": self.props.items,
            "config": {
                "selectable": self.props.selectable,
                "multi_select": self.props.multi_select,
                "searchable": self.props.searchable,
                "sortable": self.props.sortable,
                "paginated": self.props.paginated,
                "items_per_page": self.props.items_per_page,
                "virtual_scrolling": self.props.virtual_scrolling,
                "item_template": self.props.item_template,
            },
            "selected_items": self.props.value or [],
            "events": {
                "onChange": self.props.on_change,
                "onClick": self.props.on_click,
            },
            "style": self.props.style.dict(exclude_none=True),
        }


class Chart(UIComponent):
    """Chart component."""

    def __init__(self, props: ChartProps) -> dict:
        super().__init__(props)
        self.props: ChartProps = props

    def render(self) -> Dict[str, Any]:
        """Render chart component."""
        return {
            "element": "canvas",
            "attributes": {
                "id": self.props.id,
                "class": " ".join(
                    [
                        "component-chart",
                        f"chart-{self.props.chart_type}",
                        *self.props.css_classes,
                    ]
                ).strip(),
                **self.props.data_attributes,
            },
            "chart_config": {
                "type": self.props.chart_type,
                "data": self.props.data,
                "options": {
                    "responsive": self.props.responsive,
                    "animation": {"duration": 1000 if self.props.animate else 0},
                    "legend": {"position": self.props.legend_position},
                    **self.props.options,
                },
            },
            "style": self.props.style.dict(exclude_none=True),
        }


class Form(UIComponent):
    """Form component."""

    def __init__(self, props: FormProps) -> dict:
        super().__init__(props)
        self.props: FormProps = props
        self.field_components: List[UIComponent] = []

        # Create field components
        for field_props in self.props.fields:
            component = ComponentFactory.create_component(field_props)
            self.field_components.append(component)

    def render(self) -> Dict[str, Any]:
        """Render form component."""
        return {
            "element": "form",
            "attributes": {
                "id": self.props.id,
                "class": " ".join(
                    [
                        "component-form",
                        f"layout-{self.props.layout.value}",
                        *self.props.css_classes,
                    ]
                ).strip(),
                "action": self.props.submit_url,
                "method": self.props.method,
                **self.props.data_attributes,
            },
            "fields": [field.to_dict() for field in self.field_components],
            "config": {
                "layout": self.props.layout.value,
                "validate_on_blur": self.props.validate_on_blur,
                "validate_on_submit": self.props.validate_on_submit,
                "show_validation_summary": self.props.show_validation_summary,
            },
            "events": {
                "onSubmit": "handleFormSubmit",
                "onChange": self.props.on_change,
            },
            "style": self.props.style.dict(exclude_none=True),
        }

    def validate_form(self) -> bool:
        """Validate all form fields."""
        all_valid = True
        for field in self.field_components:
            if not field.validate():
                all_valid = False

        return all_valid

    def get_form_data(self) -> Dict[str, Any]:
        """Get form data as dictionary."""
        form_data = {}
        for field in self.field_components:
            if hasattr(field.props, "id") and field.props.id:
                form_data[field.props.id] = field.get_value()

        return form_data

    def set_form_data(self, data: Dict[str, Any]) -> None:
        """Set form data from dictionary."""
        for field in self.field_components:
            if hasattr(field.props, "id") and field.props.id in data:
                field.set_value(data[field.props.id])


class Modal(UIComponent):
    """Modal component."""

    def __init__(self, props: ModalProps) -> dict:
        super().__init__(props)
        self.props: ModalProps = props
        self.is_open = False

    def render(self) -> Dict[str, Any]:
        """Render modal component."""
        return {
            "element": "div",
            "attributes": {
                "id": self.props.id,
                "class": " ".join(
                    [
                        "component-modal",
                        f"modal-{self.props.size}",
                        "modal-open" if self.is_open else "",
                        *self.props.css_classes,
                    ]
                ).strip(),
                **self.props.data_attributes,
            },
            "structure": {
                "backdrop": {
                    "visible": True,
                    "dismissible": self.props.backdrop_dismiss,
                },
                "dialog": {
                    "size": self.props.size,
                    "closable": self.props.closable,
                },
                "header": {
                    "visible": self.props.header_visible,
                    "title": self.props.title,
                },
                "body": {
                    "content": self.props.content,
                },
                "footer": {
                    "visible": self.props.footer_visible,
                    "buttons": [btn.render() for btn in self.props.buttons],
                },
            },
            "events": {
                "onOpen": "handleModalOpen",
                "onClose": "handleModalClose",
            },
            "style": self.props.style.dict(exclude_none=True),
        }

    def open(self) -> None:
        """Open modal."""
        self.is_open = True

    def close(self) -> None:
        """Close modal."""
        self.is_open = False


class ComponentFactory:
    """Factory for creating UI components."""

    @staticmethod
    def create_component(props: ComponentProps) -> UIComponent:
        """Create component based on type."""
        if props.type == ComponentType.BUTTON:
            return Button(ButtonProps(**props.dict()))
        elif props.type == ComponentType.INPUT:
            return Input(InputProps(**props.dict()))
        elif props.type == ComponentType.DROPDOWN:
            return Dropdown(DropdownProps(**props.dict()))
        elif props.type == ComponentType.LIST:
            return List(ListProps(**props.dict()))
        elif props.type == ComponentType.CHART:
            return Chart(ChartProps(**props.dict()))
        elif props.type == ComponentType.FORM:
            return Form(FormProps(**props.dict()))
        elif props.type == ComponentType.MODAL:
            return Modal(ModalProps(**props.dict()))
        else:
            # Return base component for unsupported types
            return GenericComponent(props)


class GenericComponent(UIComponent):
    """Generic component for unsupported types."""

    def render(self) -> Dict[str, Any]:
        """Render generic component."""
        return {
            "element": "div",
            "attributes": {
                "id": self.props.id,
                "class": " ".join(
                    [f"component-{self.props.type.value}", *self.props.css_classes]
                ).strip(),
                **self.props.data_attributes,
            },
            "content": str(self.props.value or self.props.label or ""),
            "style": self.props.style.dict(exclude_none=True),
        }


class UIBuilder:
    """UI builder for creating component hierarchies."""

    def __init__(self, theme: Optional[Theme] = None) -> dict:
        self.theme = theme or self._get_default_theme()
        self.components: List[UIComponent] = []
        self.component_registry: Dict[str, UIComponent] = {}

    def add_component(self, component: UIComponent) -> UIBuilder:
        """Add component to builder."""
        self.components.append(component)
        self.component_registry[component.props.id] = component
        return self

    def create_button(
        self,
        label: str,
        button_type: str = "primary",
        on_click: Optional[str] = None,
        **kwargs,
    ) -> UIBuilder:
        """Create and add button component."""
        props = ButtonProps(
            label=label, button_type=button_type, on_click=on_click, **kwargs
        )
        component = Button(props)
        return self.add_component(component)

    def create_input(
        self,
        label: str,
        input_type: str = "text",
        placeholder: Optional[str] = None,
        required: bool = False,
        **kwargs,
    ) -> UIBuilder:
        """Create and add input component."""
        props = InputProps(
            label=label,
            input_type=input_type,
            placeholder=placeholder,
            required=required,
            **kwargs,
        )
        component = Input(props)
        return self.add_component(component)

    def create_dropdown(
        self,
        label: str,
        options: List[Dict[str, Any]],
        multiple: bool = False,
        searchable: bool = False,
        **kwargs,
    ) -> UIBuilder:
        """Create and add dropdown component."""
        props = DropdownProps(
            label=label,
            options=options,
            multiple=multiple,
            searchable=searchable,
            **kwargs,
        )
        component = Dropdown(props)
        return self.add_component(component)

    def create_list(
        self,
        items: List[Dict[str, Any]],
        selectable: bool = False,
        searchable: bool = False,
        **kwargs,
    ) -> UIBuilder:
        """Create and add list component."""
        props = ListProps(
            items=items, selectable=selectable, searchable=searchable, **kwargs
        )
        component = List(props)
        return self.add_component(component)

    def create_chart(
        self,
        chart_type: str,
        data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> UIBuilder:
        """Create and add chart component."""
        props = ChartProps(
            chart_type=chart_type, data=data, options=options or {}, **kwargs
        )
        component = Chart(props)
        return self.add_component(component)

    def create_form(
        self,
        fields: List[ComponentProps],
        layout: LayoutType = LayoutType.VERTICAL,
        submit_url: Optional[str] = None,
        **kwargs,
    ) -> UIBuilder:
        """Create and add form component."""
        props = FormProps(fields=fields, layout=layout, submit_url=submit_url, **kwargs)
        component = Form(props)
        return self.add_component(component)

    def create_modal(
        self,
        title: str,
        content: Optional[str] = None,
        size: str = "medium",
        buttons: Optional[List[ButtonProps]] = None,
        **kwargs,
    ) -> UIBuilder:
        """Create and add modal component."""
        props = ModalProps(
            title=title, content=content, size=size, buttons=buttons or [], **kwargs
        )
        component = Modal(props)
        return self.add_component(component)

    def get_component(self, component_id: str) -> Optional[UIComponent]:
        """Get component by ID."""
        return self.component_registry.get(component_id)

    def validate_all(self) -> bool:
        """Validate all components."""
        all_valid = True
        for component in self.components:
            if not component.validate():
                all_valid = False

        return all_valid

    def render_all(self) -> List[Dict[str, Any]]:
        """Render all components."""
        return [component.to_dict() for component in self.components]

    def to_json(self) -> str:
        """Export UI definition as JSON."""
        ui_definition = {
            "theme": self.theme.dict(),
            "components": self.render_all(),
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "component_count": len(self.components),
            },
        }

        return json.dumps(ui_definition, indent=2, default=str)

    def _get_default_theme(self) -> Theme:
        """Get default theme."""
        return Theme(name="default")


class ResponsiveLayout:
    """Responsive layout manager."""

    def __init__(self) -> dict:
        self.breakpoints = {
            "xs": 0,
            "sm": 576,
            "md": 768,
            "lg": 992,
            "xl": 1200,
            "xxl": 1400,
        }

        self.grid_columns = 12

    def create_responsive_style(
        self, styles: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create responsive CSS styles."""
        responsive_css = {}

        for breakpoint, style_props in styles.items():
            if breakpoint in self.breakpoints:
                min_width = self.breakpoints[breakpoint]

                if min_width == 0:
                    # Base styles (no media query)
                    responsive_css.update(style_props)
                else:
                    # Media query styles
                    media_query = f"@media (min-width: {min_width}px)"
                    responsive_css[media_query] = style_props

        return responsive_css

    def create_grid_layout(
        self, components: List[Dict[str, Any]], columns: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Create CSS grid layout."""
        default_columns = {"xs": 1, "sm": 2, "md": 3, "lg": 4, "xl": 6}
        grid_columns = columns or default_columns

        grid_styles = {}

        for breakpoint, cols in grid_columns.items():
            if breakpoint in self.breakpoints:
                min_width = self.breakpoints[breakpoint]

                style = {
                    "display": "grid",
                    "grid-template-columns": f"repeat({cols}, 1fr)",
                    "gap": "1rem",
                }

                if min_width == 0:
                    grid_styles.update(style)
                else:
                    media_query = f"@media (min-width: {min_width}px)"
                    grid_styles[media_query] = style

        return {
            "layout": "grid",
            "styles": grid_styles,
            "components": components,
        }

    def create_flex_layout(
        self,
        components: List[Dict[str, Any]],
        direction: str = "column",
        wrap: bool = True,
        justify: str = "flex-start",
        align: str = "stretch",
    ) -> Dict[str, Any]:
        """Create flexbox layout."""
        flex_styles = {
            "display": "flex",
            "flex-direction": direction,
            "flex-wrap": "wrap" if wrap else "nowrap",
            "justify-content": justify,
            "align-items": align,
            "gap": "1rem",
        }

        return {
            "layout": "flex",
            "styles": flex_styles,
            "components": components,
        }


class UIModule:
    """Main UI module for SDK."""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self.theme_manager = ThemeManager()
        self.component_library = ComponentLibrary()
        self.layout_manager = ResponsiveLayout()

        # Pre-built templates
        self.templates = UITemplates()

    async def initialize(self) -> None:
        """Initialize UI module."""
        # Load theme from server or use default
        await self._load_theme()

        # Register module with SDK
        self.sdk.register_module("ui", self)

    async def _load_theme(self) -> None:
        """Load theme configuration."""
        try:
            response = await self.sdk.http_client.get(
                "ui/theme", params={"organization_id": self.sdk.config.organization_id}
            )

            if response["status"] == 200:
                theme_data = response["data"]
                theme = Theme(**theme_data)
                self.theme_manager.set_active_theme(theme)
        except Exception as e:
            print(f"[SDK] Failed to load theme: {e}")
            # Use default theme
            self.theme_manager.set_active_theme(Theme(name="default"))

    def create_builder(self, theme: Optional[Theme] = None) -> UIBuilder:
        """Create UI builder."""
        active_theme = theme or self.theme_manager.get_active_theme()
        return UIBuilder(active_theme)

    def create_component(self, component_type: ComponentType, **props) -> UIComponent:
        """Create individual component."""
        component_props = self._create_component_props(component_type, **props)
        return ComponentFactory.create_component(component_props)

    def _create_component_props(
        self, component_type: ComponentType, **props
    ) -> ComponentProps:
        """Create component properties based on type."""
        if component_type == ComponentType.BUTTON:
            return ButtonProps(type=component_type, **props)
        elif component_type == ComponentType.INPUT:
            return InputProps(type=component_type, **props)
        elif component_type == ComponentType.DROPDOWN:
            return DropdownProps(type=component_type, **props)
        elif component_type == ComponentType.LIST:
            return ListProps(type=component_type, **props)
        elif component_type == ComponentType.CHART:
            return ChartProps(type=component_type, **props)
        elif component_type == ComponentType.FORM:
            return FormProps(type=component_type, **props)
        elif component_type == ComponentType.MODAL:
            return ModalProps(type=component_type, **props)
        else:
            return ComponentProps(type=component_type, **props)

    def get_templates(self) -> UITemplates:
        """Get pre-built UI templates."""
        return self.templates

    def get_theme_manager(self) -> ThemeManager:
        """Get theme manager."""
        return self.theme_manager

    def get_layout_manager(self) -> ResponsiveLayout:
        """Get layout manager."""
        return self.layout_manager


class ThemeManager:
    """Theme management system."""

    def __init__(self) -> dict:
        self.themes: Dict[str, Theme] = {}
        self.active_theme: Optional[Theme] = None

        # Add default themes
        self._load_default_themes()

    def _load_default_themes(self) -> None:
        """Load default themes."""
        # Light theme
        light_theme = Theme(name="light", mode=ThemeMode.LIGHT)
        self.themes["light"] = light_theme

        # Dark theme
        dark_theme = Theme(
            name="dark",
            mode=ThemeMode.DARK,
            background_primary="#1C1C1E",
            background_secondary="#2C2C2E",
            text_primary="#FFFFFF",
            text_secondary="#EBEBF5",
            border_primary="#38383A",
        )
        self.themes["dark"] = dark_theme

        # Set light as default
        self.active_theme = light_theme

    def add_theme(self, theme: Theme) -> None:
        """Add custom theme."""
        self.themes[theme.name] = theme

    def set_active_theme(self, theme: Union[Theme, str]) -> None:
        """Set active theme."""
        if isinstance(theme, str):
            if theme in self.themes:
                self.active_theme = self.themes[theme]
            else:
                raise ValueError(f"Theme '{theme}' not found")
        else:
            self.active_theme = theme

    def get_active_theme(self) -> Theme:
        """Get active theme."""
        return self.active_theme or self.themes["light"]

    def get_theme(self, name: str) -> Optional[Theme]:
        """Get theme by name."""
        return self.themes.get(name)

    def list_themes(self) -> List[str]:
        """List available theme names."""
        return list(self.themes.keys())


class ComponentLibrary:
    """Component library with pre-configured components."""

    def __init__(self) -> dict:
        self.components: Dict[str, Dict[str, Any]] = {}
        self._load_component_library()

    def _load_component_library(self) -> None:
        """Load component library."""
        self.components = {
            "primary_button": {
                "type": ComponentType.BUTTON,
                "props": {
                    "button_type": "primary",
                    "size": "medium",
                    "style": ComponentStyle(
                        border_radius=8, padding={"vertical": 12, "horizontal": 24}
                    ),
                },
            },
            "search_input": {
                "type": ComponentType.INPUT,
                "props": {
                    "input_type": "text",
                    "placeholder": "Search...",
                    "style": ComponentStyle(
                        border_radius=20, padding={"vertical": 8, "horizontal": 16}
                    ),
                },
            },
            "data_table": {
                "type": ComponentType.TABLE,
                "props": {
                    "sortable": True,
                    "filterable": True,
                    "paginated": True,
                    "page_size": 25,
                    "striped": True,
                },
            },
        }

    def get_component_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get component configuration."""
        return self.components.get(name)

    def create_component(self, name: str, **override_props) -> Optional[UIComponent]:
        """Create component from library."""
        config = self.get_component_config(name)
        if not config:
            return None

        # Merge override props
        props = {**config["props"], **override_props}
        component_props = ComponentProps(type=config["type"], **props)

        return ComponentFactory.create_component(component_props)


class UITemplates:
    """Pre-built UI templates."""

    def create_login_form(self) -> UIBuilder:
        """Create login form template."""
        builder = UIBuilder()

        builder.create_input(
            label="Email",
            input_type="email",
            placeholder="Enter your email",
            required=True,
            id="email",
        ).create_input(
            label="Password",
            input_type="password",
            placeholder="Enter your password",
            required=True,
            id="password",
        ).create_button(
            label="Sign In", button_type="primary", submit=True, on_click="handleLogin"
        )

        return builder

    def create_data_list(self, items: List[Dict[str, Any]]) -> UIBuilder:
        """Create data list template."""
        builder = UIBuilder()

        builder.create_input(
            label="Search",
            input_type="text",
            placeholder="Search items...",
            id="search",
            on_change="handleSearch",
        ).create_list(items=items, selectable=True, searchable=True, paginated=True)

        return builder

    def create_dashboard_layout(self) -> UIBuilder:
        """Create dashboard layout template."""
        builder = UIBuilder()

        # Summary cards
        builder.create_chart(
            chart_type="doughnut",
            data={
                "labels": ["Completed", "Pending", "Overdue"],
                "datasets": [
                    {
                        "data": [45, 35, 20],
                        "backgroundColor": ["#34C759", "#FF9500", "#FF3B30"],
                    }
                ],
            },
            id="status_chart",
        )

        # Data table
        builder.create_chart(
            chart_type="line",
            data={
                "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
                "datasets": [
                    {
                        "label": "Performance",
                        "data": [65, 59, 80, 81, 56],
                        "borderColor": "#007AFF",
                    }
                ],
            },
            id="performance_chart",
        )

        return builder

    def create_settings_form(self) -> UIBuilder:
        """Create settings form template."""
        builder = UIBuilder()

        builder.create_input(
            label="Display Name", input_type="text", id="display_name"
        ).create_dropdown(
            label="Theme",
            options=[
                {"label": "Light", "value": "light"},
                {"label": "Dark", "value": "dark"},
                {"label": "Auto", "value": "auto"},
            ],
            id="theme",
        ).create_dropdown(
            label="Language",
            options=[
                {"label": "English", "value": "en"},
                {"label": "Japanese", "value": "ja"},
                {"label": "Spanish", "value": "es"},
            ],
            id="language",
        ).create_button(
            label="Save Settings",
            button_type="primary",
            submit=True,
            on_click="handleSaveSettings",
        )

        return builder
