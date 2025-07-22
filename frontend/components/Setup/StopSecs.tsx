import React, { useEffect, useState } from "react";

import { useDebounce } from "@uidotdev/usehooks";
import HelpTip from "../ui/helptip";
import { Label } from "../ui/label";
import { Slider } from "../ui/slider";

interface StopSecsProps {
  label: string;
  helpText: string;
  value: number;
  handleChange: (value: number) => void;
  postfix?: string;
}

const StopSecs: React.FC<StopSecsProps> = ({
  label,
  helpText,
  value = 0.3,
  postfix = "",
  handleChange,
}) => {
  const [stopSecs, setStopSecs] = useState<number>(value);
  const debouncedUpdate = useDebounce(stopSecs, 500);

  const handleValueChange = (value: number[]) => {
    if (value[0] === stopSecs) return;
    setStopSecs(value[0]);
  };

  useEffect(() => {
    if (debouncedUpdate !== value) {
      handleChange(debouncedUpdate);
    }
  }, [debouncedUpdate, handleChange, value]);

  return (
    <div className="flex flex-col justify-between gap-2">
      <Label className="flex flex-row gap-1 items-center shrink-0">
        {label}
        <HelpTip text={helpText} />
      </Label>
      <div className="flex flex-row gap-2">
        <Slider
          value={[stopSecs]}
          min={0.1}
          max={2}
          step={0.1}
          onValueChange={handleValueChange}
        />
        <div className="w-24">
          {stopSecs}
          {postfix}
        </div>
      </div>
    </div>
  );
};

export default StopSecs;
