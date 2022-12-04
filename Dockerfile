ARG MODE=label

ARG DONE_SOON_VENV=/opt/done_soon-venv
ARG DONE_SOON_PYTHON=${DONE_SOON_VENV}/bin/python
ARG DONE_SOON_PIP=${DONE_SOON_VENV}/bin/pip

ARG BASE_IMAGE=ubuntu:20.04
ARG MINIZINCVERSION=2.6.4

ARG DEBIAN_FRONTEND=noninteractive

FROM ${BASE_IMAGE} AS with_python_pip
ARG DONE_SOON_VENV
ENV PIP_ROOT_USER_ACTION=ignore
ADD https://bootstrap.pypa.io/get-pip.py get-pip.py
# Install python3.10
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install software-properties-common -y && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get install -y \
        python3.10 \
        python3.10-venv && \
    # Install pip
    python3.10 get-pip.py && \
    rm get-pip.py && \
    python3.10 -m venv ${DONE_SOON_VENV}


FROM ${BASE_IMAGE} AS with_minizinc
ARG MINIZINCVERSION
# Install MiniZinc
ADD https://github.com/MiniZinc/MiniZincIDE/releases/download/${MINIZINCVERSION}/MiniZincIDE-${MINIZINCVERSION}-bundle-linux-x86_64.tgz MiniZincIDE-${MINIZINCVERSION}-bundle-linux-x86_64.tgz
RUN tar xf MiniZincIDE-${MINIZINCVERSION}-bundle-linux-x86_64.tgz && \
    rm MiniZincIDE-${MINIZINCVERSION}-bundle-linux-x86_64.tgz


FROM ${BASE_IMAGE} AS with_modded_chuffed
ARG ROOTDIR
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y \
        build-essential \
        cmake
COPY ./chuffed ${ROOTDIR}/chuffed
WORKDIR ${ROOTDIR}/chuffed/build
RUN cmake .. && \
    cmake --build . -j $(nproc) --target install


FROM with_python_pip AS generate_requirements_txts
ARG ROOTDIR
# Install poetry separated from system interpreter
ENV POETRY_VERSION=1.2.0
ENV POETRY_VENV=/opt/poetry-venv
RUN python3.10 -m venv ${POETRY_VENV} && \
    $POETRY_VENV/bin/pip install -U setuptools && \
    $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}
ENV PATH="${PATH}:${POETRY_VENV}/bin"
WORKDIR ${ROOTDIR}
COPY ./pyproject.toml .
COPY ./poetry.lock .
RUN poetry export --with=download -o requirements-download.txt && \
    poetry export -o requirements.txt && \
    rm ./pyproject.toml ./poetry.lock


FROM with_python_pip AS with_problems
ARG ROOTDIR
ARG DONE_SOON_PYTHON
ARG DONE_SOON_PIP
ARG PROBLEM_SOURCE
WORKDIR ${ROOTDIR}
COPY --from=generate_requirements_txts ${ROOTDIR}/requirements-download.txt .
COPY ./problems/download.py ${ROOTDIR}/problems/download.py
COPY ./problems/convert_cnf.py ${ROOTDIR}/problems/convert_cnf.py
RUN ${DONE_SOON_PIP} install -r requirements-download.txt && \
    ${DONE_SOON_PYTHON} problems/download.py \
                    --destination problems/problem_sets --source ${PROBLEM_SOURCE} && \
    ${DONE_SOON_PYTHON} problems/convert_cnf.py -c problems/problem_sets/satlib/cnf \
                                                -o problems/problem_sets/satlib


FROM with_python_pip AS with_dependencies
ARG ROOTDIR
ARG DONE_SOON_PIP
WORKDIR ${ROOTDIR}
COPY --from=generate_requirements_txts ${ROOTDIR}/requirements.txt .
RUN ${DONE_SOON_PIP} install -r requirements.txt


FROM with_problems AS seed_db
ARG ROOTDIR
ARG DONE_SOON_PIP
ARG DONE_SOON_PYTHON
WORKDIR ${ROOTDIR}
COPY --from=generate_requirements_txts ${ROOTDIR}/requirements.txt .
RUN ${DONE_SOON_PIP} install -r requirements.txt
COPY ./done_soon/ ./done_soon/
ENV PYTHONPATH="${PYTHONPATH}:${ROOTDIR}" DONE_SOON_PYTHON=${DONE_SOON_PYTHON} ROOTDIR=${ROOTDIR}
CMD ${DONE_SOON_PYTHON} ${ROOTDIR}/done_soon/data_generation/db/scripts/create_initial_db.py \
    --data problems/problem_sets --db-addr mongodb


FROM with_python_pip AS data_generator
ARG ROOTDIR
ARG MINIZINCVERSION
ARG DONE_SOON_PYTHON
ARG MODE
ARG MODDED_CHUFFED_INSTALL_PREFIX
ARG MINIZINC_DIR="/MiniZincIDE-${MINIZINCVERSION}-bundle-linux-x86_64/"
COPY --from=with_dependencies ${DONE_SOON_VENV} ${DONE_SOON_VENV}
COPY --from=with_problems ${ROOTDIR}/problems/ ${ROOTDIR}/problems/
COPY --from=with_modded_chuffed /usr/local/share/minizinc /usr/local/share/minizinc
COPY --from=with_modded_chuffed /usr/local/bin/fzn-modded-chuffed /usr/local/bin/fzn-modded-chuffed
COPY --from=with_minizinc ${MINIZINC_DIR} ${MINIZINC_DIR}

# Copy the rest of the project source in
WORKDIR ${ROOTDIR}
COPY ./done_soon ./done_soon
ENV PATH="${MINIZINC_DIR}/bin:${PATH}" PYTHONPATH="${PYTHONPATH}:${ROOTDIR}"
ENV DONE_SOON_PYTHON=${DONE_SOON_PYTHON} ROOTDIR=${ROOTDIR} MODE=${MODE}

WORKDIR ${ROOTDIR}
CMD ${DONE_SOON_PYTHON} ${ROOTDIR}/done_soon/data_generation/generate_data.py  \
    --mode ${MODE} \
    --data problems/problem_sets \
    --db-addr mongodb
