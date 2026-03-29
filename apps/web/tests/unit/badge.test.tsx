import { render, screen } from "@testing-library/react";

import { Badge } from "@/components/ui/badge";

describe("Badge", () => {
  it("renders badge content", () => {
    render(<Badge tone="high">high</Badge>);
    expect(screen.getByText("high")).toBeInTheDocument();
  });
});
