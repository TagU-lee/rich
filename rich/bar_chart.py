"""Bar chart renderable for Rich."""

from typing import (
    TYPE_CHECKING,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from .bar import END_BLOCK_ELEMENTS, FULL_BLOCK
from .console import Console, ConsoleOptions, RenderResult
from .jupyter import JupyterMixin
from .measure import Measurement
from .segment import Segment
from .style import Style, StyleType

if TYPE_CHECKING:
    from .color import Color


class BarChart(JupyterMixin):
    """Renders a bar chart with multiple bars.

    Args:
        data (Union[Dict[str, float], List[Tuple[str, float]], Sequence[float]]): 
            Data to display. Can be:
            - Dict mapping labels to values
            - List of (label, value) tuples
            - Sequence of values (labels will be auto-generated)
        width (int, optional): Width of the chart, or None for maximum width. Defaults to None.
        max_value (float, optional): Maximum value for scaling. If None, uses max value from data. Defaults to None.
        show_values (bool, optional): Show values on bars. Defaults to True.
        bar_width (int, optional): Width of each bar in characters. Defaults to 1.
        style (StyleType, optional): Default style for bars. Defaults to None.
        bar_styles (Sequence[StyleType], optional): Styles for each bar (cycled if fewer than bars). Defaults to None.
        label_style (StyleType, optional): Style for labels. Defaults to None.
        value_style (StyleType, optional): Style for values. Defaults to None.
    """

    def __init__(
        self,
        data: Union[Dict[str, float], List[Tuple[str, float]], Sequence[float]],
        *,
        width: Optional[int] = None,
        max_value: Optional[float] = None,
        show_values: bool = True,
        bar_width: int = 1,
        style: Optional[StyleType] = None,
        bar_styles: Optional[Sequence[StyleType]] = None,
        label_style: Optional[StyleType] = None,
        value_style: Optional[StyleType] = None,
    ):
        # Normalize data to list of (label, value) tuples
        if isinstance(data, dict):
            self.items = list(data.items())
        elif isinstance(data, list) and data and isinstance(data[0], tuple):
            self.items = data
        else:
            # Sequence of values - generate labels
            self.items = [(str(i), float(v)) for i, v in enumerate(data)]

        if not self.items:
            raise ValueError("Data cannot be empty")

        self.width = width
        self.show_values = show_values
        self.bar_width = bar_width
        self.style = style
        self.bar_styles = list(bar_styles) if bar_styles else None
        self.label_style = label_style
        self.value_style = value_style

        # Calculate max value
        values = [value for _, value in self.items]
        self.max_value = max_value if max_value is not None else max(values)
        if self.max_value <= 0:
            self.max_value = 1.0

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Render the bar chart."""
        available_width = (
            self.width if self.width is not None else options.max_width
        )
        available_width = min(available_width, options.max_width)

        # Calculate label width
        max_label_len = max(len(str(label)) for label, _ in self.items)
        label_width = max_label_len + 2  # Add padding

        # Calculate bar area width
        bar_area_width = available_width - label_width
        if self.show_values:
            # Reserve space for values (estimate: max 10 chars + 1 space)
            bar_area_width -= 12

        if bar_area_width < 1:
            bar_area_width = 1

        # Default colors if no styles provided
        default_colors = [
            "blue",
            "green",
            "yellow",
            "magenta",
            "cyan",
            "red",
            "bright_blue",
            "bright_green",
        ]

        for idx, (label, value) in enumerate(self.items):
            # Get style for this bar
            if self.bar_styles:
                bar_style = self.bar_styles[idx % len(self.bar_styles)]
            elif self.style:
                bar_style = self.style
            else:
                bar_style = default_colors[idx % len(default_colors)]

            # Calculate bar length
            if self.max_value > 0:
                bar_length = int((value / self.max_value) * bar_area_width)
            else:
                bar_length = 0

            # Create label text
            label_str = str(label)
            label_padding = " " * (label_width - len(label_str) - 1)
            label_style_obj = Style.parse(str(self.label_style)) if self.label_style else None

            # Create bar
            full_blocks = bar_length // self.bar_width
            remainder = bar_length % self.bar_width

            bar_chars = FULL_BLOCK * full_blocks
            if remainder > 0 and remainder < len(END_BLOCK_ELEMENTS):
                bar_chars += END_BLOCK_ELEMENTS[remainder]

            # Create value text if needed
            value_text = ""
            if self.show_values:
                if isinstance(value, float):
                    value_text = f" {value:.2f}"
                else:
                    value_text = f" {value}"

            # Combine label, bar, and value
            line_segments: List[Segment] = []
            line_segments.append(Segment(label_padding))
            line_segments.append(Segment(label_str, label_style_obj))
            line_segments.append(Segment(" "))
            line_segments.append(Segment(bar_chars, Style.parse(str(bar_style))))
            if value_text:
                value_style_obj = Style.parse(str(self.value_style)) if self.value_style else None
                line_segments.append(Segment(value_text, value_style_obj))
            line_segments.append(Segment.line())

            yield from line_segments

    def __rich_measure__(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        """Measure the bar chart."""
        if self.width is not None:
            return Measurement(self.width, self.width)
        return Measurement(20, options.max_width)

