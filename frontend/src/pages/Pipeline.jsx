import { useEffect, useState } from "react";
import { getPipelineStatus } from "../api/analyticsApi";
import LoadingSkeleton from "../components/LoadingSkeleton";
import { formatDateTime } from "../utils/formatters";

function Pipeline() {
    const [pipeline, setPipeline] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState("");

    useEffect(() => {
        async function loadPipelineStatus() {
            try {
                const pipelineData = await getPipelineStatus();
                setPipeline(pipelineData);
            } catch (error) {
                console.error("Unable to load pipeline status.", error);
                setErrorMessage("Unable to load pipeline status.");
            } finally {
                setIsLoading(false);
            }
        }

        loadPipelineStatus();
    }, []);

    if (isLoading) {
        return (
            <section>
                <div className="page-header">
                    <div>
                        <p className="eyebrow">Data Engineering View</p>
                        <h1>Pipeline Status</h1>
                        <p>Loading pipeline metadata from FastAPI...</p>
                    </div>
                </div>

                <LoadingSkeleton rows={3} />
            </section>
        );
    }

    if (errorMessage) {
        return (
            <section>
                <div className="page-header">
                    <div>
                        <p className="eyebrow">Data Engineering View</p>
                        <h1>Pipeline Status</h1>
                    </div>
                </div>

                <p className="error-message">{errorMessage}</p>
            </section>
        );
    }

    return (
        <section>
            <div className="page-header">
                <div>
                    <p className="eyebrow">Data Engineering View</p>
                    <h1>Pipeline Status</h1>
                    <p>
                        End-to-end AWS data flow powering the RetailLens analytics dashboard.
                    </p>
                </div>

                <div className="source-pill">
                    <span>API status</span>
                    <strong>{pipeline?.status || "ok"}</strong>
                </div>
            </div>

            <div className="pipeline-flow polished-flow">
                <div>
                    <span>1</span>
                    S3 Raw
                </div>
                <span>→</span>
                <div>
                    <span>2</span>
                    Glue ETL
                </div>
                <span>→</span>
                <div>
                    <span>3</span>
                    S3 Parquet
                </div>
                <span>→</span>
                <div>
                    <span>4</span>
                    Athena
                </div>
                <span>→</span>
                <div>
                    <span>5</span>
                    DynamoDB
                </div>
                <span>→</span>
                <div>
                    <span>6</span>
                    FastAPI
                </div>
                <span>→</span>
                <div>
                    <span>7</span>
                    React
                </div>
            </div>

            <div className="kpi-grid kpi-grid-three">
                <div className="kpi-card">
                    <p className="kpi-label">AWS Region</p>
                    <h2 className="kpi-value kpi-value-small">
                        {pipeline?.aws_region || "us-west-2"}
                    </h2>
                </div>

                <div className="kpi-card">
                    <p className="kpi-label">Serving Table</p>
                    <h2 className="kpi-value kpi-value-small">
                        {pipeline?.dynamodb_table || "N/A"}
                    </h2>
                </div>

                <div className="kpi-card">
                    <p className="kpi-label">Last Metrics Refresh</p>
                    <h2 className="kpi-value kpi-value-small">
                        {formatDateTime(pipeline?.last_updated)}
                    </h2>
                </div>
            </div>

            <div className="panel">
                <div className="panel-header">
                    <div>
                        <h2>AWS Resource Metadata</h2>
                        <p>
                            Metadata stored in DynamoDB for the frontend pipeline view.
                        </p>
                    </div>
                </div>

                <div className="metadata-grid">
                    <div className="metadata-item">
                        <span>Status</span>
                        <strong>{pipeline?.status}</strong>
                    </div>

                    <div className="metadata-item">
                        <span>Raw Glue Database</span>
                        <strong>{pipeline?.raw_database}</strong>
                    </div>

                    <div className="metadata-item">
                        <span>Curated Glue Database</span>
                        <strong>{pipeline?.curated_database}</strong>
                    </div>

                    <div className="metadata-item">
                        <span>Curated Table</span>
                        <strong>{pipeline?.curated_table}</strong>
                    </div>

                    <div className="metadata-item metadata-wide">
                        <span>S3 Curated Path</span>
                        <strong>{pipeline?.s3_curated_path}</strong>
                    </div>

                    <div className="metadata-item metadata-wide">
                        <span>Athena Output Location</span>
                        <strong>{pipeline?.athena_output_location}</strong>
                    </div>
                </div>
            </div>

            <div className="panel architecture-panel">
                <div className="panel-header">
                    <div>
                        <h2>Architecture Summary</h2>
                        <p>
                            Raw retail CSV data is transformed into analytics-ready metrics
                            through AWS data lake services and served to the React dashboard.
                        </p>
                    </div>
                </div>

                <div className="architecture-list">
                    <div>
                        <strong>S3 Raw Zone</strong>
                        <p>Stores generated retail CSV files for customers, orders, products, payments, and refunds.</p>
                    </div>

                    <div>
                        <strong>Glue + PySpark</strong>
                        <p>Cleans, joins, and transforms raw data into curated partitioned Parquet.</p>
                    </div>

                    <div>
                        <strong>Athena Aggregations</strong>
                        <p>Computes summary, revenue, product, regional, and refund metrics over curated data.</p>
                    </div>

                    <div>
                        <strong>DynamoDB Serving Layer</strong>
                        <p>Stores precomputed metrics for fast API responses.</p>
                    </div>

                    <div>
                        <strong>FastAPI + React</strong>
                        <p>Exposes analytics endpoints and visualizes the data in a recruiter-facing dashboard.</p>
                    </div>
                </div>
            </div>
        </section>
    );
}

export default Pipeline;